import dotenv from "dotenv";
import { performance } from "perf_hooks";
import pg from "pg";

dotenv.config();

// Database connection configs using DATABASE_URL
const sourceDb = new pg.Pool({
  connectionString: process.env.SOURCE_DATABASE_URL,
});

const targetDb = new pg.Pool({
  connectionString: process.env.TARGET_DATABASE_URL,
});

// Table migration order to handle foreign key dependencies
const TABLE_MIGRATION_ORDER = [
  "users",
  "telegram_messages",
  "edgelord",
  "edgelord_oneoff",
  "hitchiker_conversations",
  "narratives",
  "ducky_ai",
  "tweet_replies",
  "mentioned_tweets",
];

const BATCH_SIZE = 1000;

interface MigrationResult {
  table: string;
  rowCount: number;
  timeElapsed: number;
  error?: string;
}

async function getRowCount(db: pg.Pool, table: string): Promise<number> {
  try {
    const result = await db.query(`SELECT COUNT(*) FROM ${table}`);
    return parseInt(result.rows[0].count);
  } catch (error) {
    console.error(`Error getting row count for ${table}:`, error);
    return 0;
  }
}

async function migrateTable(table: string): Promise<MigrationResult> {
  const startTime = performance.now();
  let rowCount = 0;

  try {
    console.log(`Starting migration of table: ${table}`);

    // Get total count of rows
    const totalRows = await getRowCount(sourceDb, table);
    console.log(`Total rows to migrate in ${table}: ${totalRows}`);

    // Get column names
    const columnsResult = await sourceDb.query(
      `
      SELECT column_name 
      FROM information_schema.columns 
      WHERE table_name = $1
      ORDER BY ordinal_position
    `,
      [table]
    );

    const columnNames = columnsResult.rows.map((row: any) => row.column_name);
    const columnList = columnNames.join(", ");

    // Process in batches
    for (let offset = 0; offset < totalRows; offset += BATCH_SIZE) {
      const batchQuery = `
        SELECT * FROM ${table}
        ORDER BY ${getOrderByColumn(table)}
        LIMIT ${BATCH_SIZE} OFFSET ${offset}
      `;

      const batch = await sourceDb.query(batchQuery);

      if (batch.rows.length > 0) {
        // Create parameterized values for INSERT
        const values = batch.rows.map((row: any) =>
          columnNames.map((col: any) => row[col])
        );

        const placeholders = values
          .map(
            (_: any, i: number) =>
              `(${columnNames
                .map(
                  (_: any, j: number) => `$${i * columnNames.length + j + 1}`
                )
                .join(", ")})`
          )
          .join(", ");

        const insertQuery = `
          INSERT INTO ${table} (${columnList})
          VALUES ${placeholders}
          ON CONFLICT DO NOTHING
        `;

        // Flatten values array for parameterized query
        const flatValues = values.flat();

        await targetDb.query(insertQuery, flatValues);
        rowCount += batch.rows.length;

        console.log(`Migrated ${rowCount}/${totalRows} rows in ${table}`);
      }
    }

    // Reset sequences if needed
    if (hasSerialColumn(table)) {
      await resetSequence(table);
    }

    const timeElapsed = (performance.now() - startTime) / 1000;
    return { table, rowCount, timeElapsed };
  } catch (error) {
    console.error(`Error migrating ${table}:`, error);
    return {
      table,
      rowCount,
      timeElapsed: (performance.now() - startTime) / 1000,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

function getOrderByColumn(table: string): string {
  const orderColumns: Record<string, string> = {
    followers: "id",
    followers_history: "id",
    follower_sync_runs: "id",
    users: "id",
    telegram_messages: "message_id",
    edgelord: "id",
    edgelord_oneoff: "id",
    hitchiker_conversations: "id",
    narratives: "id",
    price_data: "id",
    rate_limit: "ip_address",
    ducky_ai: "id",
    tweet_replies: "id",
    mentioned_tweets: "id",
  };

  return orderColumns[table] || "id";
}

function hasSerialColumn(table: string): boolean {
  const tablesWithSerial = [
    "edgelord",
    "edgelord_oneoff",
    "hitchiker_conversations",
    "narratives",
    "ducky_ai",
    "followers_history",
    "follower_sync_runs",
    "users",
  ];

  return tablesWithSerial.includes(table);
}

async function resetSequence(table: string): Promise<void> {
  try {
    await targetDb.query(`
      SELECT setval(pg_get_serial_sequence('${table}', 'id'),
        (SELECT COALESCE(MAX(id), 0) FROM ${table}), true)
    `);
  } catch (error) {
    console.error(`Error resetting sequence for ${table}:`, error);
  }
}

async function main() {
  const startTime = performance.now();
  const results: MigrationResult[] = [];

  try {
    // Disable triggers and foreign key constraints in target database
    await targetDb.query("SET session_replication_role = replica;");

    // Migrate each table
    for (const table of TABLE_MIGRATION_ORDER) {
      const result = await migrateTable(table);
      results.push(result);
    }

    // Re-enable triggers and foreign key constraints
    await targetDb.query("SET session_replication_role = DEFAULT;");

    // Print summary
    console.log("\nMigration Summary:");
    console.log("------------------");
    results.forEach((result) => {
      const status = result.error ? "❌" : "✅";
      console.log(`${status} ${result.table}:`);
      console.log(`   Rows: ${result.rowCount.toLocaleString()}`);
      console.log(`   Time: ${result.timeElapsed.toFixed(2)}s`);
      if (result.error) {
        console.log(`   Error: ${result.error}`);
      }
    });

    const totalTime = (performance.now() - startTime) / 1000;
    const totalRows = results.reduce((sum, r) => sum + r.rowCount, 0);
    console.log("\nTotal Statistics:");
    console.log(`Total rows migrated: ${totalRows.toLocaleString()}`);
    console.log(`Total time: ${totalTime.toFixed(2)}s`);
  } catch (error) {
    console.error("Migration failed:", error);
  } finally {
    // Close database connections
    await sourceDb.end();
    await targetDb.end();
  }
}

// Run the migration
main().catch(console.error);
