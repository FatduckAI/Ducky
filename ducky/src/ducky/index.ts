import { CronJob } from "cron";
import parse from "cronstrue";

interface DuckyTask {
  name: string;
  cronPattern: string;
  description?: string;
  task: () => Promise<void> | void;
}

export class Ducky {
  private tasks: Map<string, CronJob>;
  private runningTasks: Set<string>;
  private taskList: DuckyTask[];
  private isTestMode: boolean = false;
  private isHelpMode: boolean = false;
  private testTaskNumber?: number;

  constructor() {
    this.tasks = new Map();
    this.runningTasks = new Set();
    this.taskList = [];
    this.setupShutdownHandlers();
    this.processArguments();
  }

  private processArguments(): void {
    // Use Bun's built-in arg parser
    const args = Bun.argv;
    this.isTestMode = args.includes("--test") || args.includes("-t");
    this.isHelpMode = args.includes("--help") || args.includes("-h");

    const taskIndex = args.findIndex((arg) => arg === "--task" || arg === "-n");
    if (taskIndex !== -1 && args[taskIndex + 1]) {
      this.testTaskNumber = parseInt(args[taskIndex + 1], 10) - 1;
    }
  }

  public addTask(config: DuckyTask): boolean {
    try {
      this.taskList.push(config);
      const taskNumber = this.taskList.length;

      if (!this.isTestMode && !this.isHelpMode) {
        const task = new CronJob(config.cronPattern, async () => {
          await this.executeTask(config);
        });
        this.tasks.set(config.name, task);
        console.log(`🦆 Added task ${taskNumber}: ${config.name}`);
      }
      return true;
    } catch (error) {
      console.error(`🦆 Error adding task ${config.name}:`, error);
      return false;
    }
  }

  private printHelp(): void {
    console.log("\n🦆 Ducky Task Manager - Available Commands:");
    console.log("----------------------------------------");
    console.log("Run normally:");
    console.log("  bun run index.ts");
    console.log("\nTest mode:");
    console.log("  --test, -t           Enter test mode");
    console.log("  --task <n>, -n <n>   Run specific task number");
    console.log("  --help, -h           Show this help message");
    console.log("\n🦆 Registered Tasks:");
    console.log("----------------------------------------");

    const longestNameLength = Math.max(
      ...this.taskList.map((t) => t.name.length)
    );
    const longestCronLength = Math.max(
      ...this.taskList.map((t) => t.cronPattern.length)
    );

    this.taskList.forEach((task, index) => {
      const number = `${index + 1}.`.padEnd(4);
      const name = task.name.padEnd(longestNameLength + 2);
      const cron = task.cronPattern.padEnd(longestCronLength + 2);
      const schedule = parse.toString(task.cronPattern);
      console.log(`${number}${name}${cron}(${schedule})`);
      if (task.description) {
        console.log(`    └─ ${task.description}`);
      }
    });
    console.log("\n🦆 Example usage:");
    console.log("----------------------------------------");
    console.log("Run in test mode:    bun run index.ts --test");
    console.log("Test specific task:  bun run index.ts --test --task 1");
    console.log("Show this help:      bun run index.ts --help\n");
  }

  private async executeTask(config: DuckyTask): Promise<void> {
    if (this.runningTasks.has(config.name)) {
      console.log(`🦆 Task ${config.name} is already running, skipping...`);
      return;
    }

    try {
      this.runningTasks.add(config.name);
      console.log(`🦆 Starting task: ${config.name}`);

      await config.task();

      console.log(`🦆 Completed task: ${config.name}`);
    } catch (error) {
      console.error(`🦆 Error in task ${config.name}:`, error);
    } finally {
      this.runningTasks.delete(config.name);
    }
  }

  public async start(): Promise<void> {
    // Always show task list at startup
    if (!this.isHelpMode) {
      console.log("\n🦆 Starting Ducky with the following tasks:");
      console.log("----------------------------------------");
      this.taskList.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name} (${task.cronPattern})`);
      });
      console.log("----------------------------------------\n");
    }

    if (this.isHelpMode) {
      this.printHelp();
      process.exit(0);
    } else if (this.isTestMode) {
      await this.runTestMode();
    } else {
      this.startAll();
    }
  }

  private async runTestMode(): Promise<void> {
    if (this.testTaskNumber !== undefined) {
      if (
        this.testTaskNumber >= 0 &&
        this.testTaskNumber < this.taskList.length
      ) {
        const taskToRun = this.taskList[this.testTaskNumber];
        console.log(`🦆 Running test task: ${taskToRun.name}`);
        await this.executeTask(taskToRun);
        console.log("🦆 Test complete! Quitting...");
      } else {
        console.error(
          `🦆 Invalid task number! Please choose 1-${this.taskList.length}`
        );
      }
      process.exit(0);
    } else {
      console.log(
        "🦆 No task specified. Use --task <number> to run a specific task"
      );
      this.printHelp();
      process.exit(0);
    }
  }

  public startAll(): void {
    this.tasks.forEach((task, name) => {
      task.start();
      console.log(`🦆 Started task: ${name}`);
    });
    console.log("🦆 All tasks are swimming!");
  }

  public stopAll(): void {
    this.tasks.forEach((task, name) => {
      task.stop();
      console.log(`🦆 Stopped task: ${name}`);
    });
    console.log("🦆 All tasks have returned to the pond");
  }

  private setupShutdownHandlers(): void {
    process.on("SIGTERM", () => this.handleShutdown());
    process.on("SIGINT", () => this.handleShutdown());
  }

  private handleShutdown(): void {
    console.log("🦆 Time to swim home! Shutting down...");
    this.stopAll();
    process.exit(0);
  }
}
