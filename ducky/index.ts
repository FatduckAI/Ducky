import { Ducky } from "./src/ducky";
import { main as contributorMain } from "./src/services/contributions/contributor";

// Create Ducky instance
const ducky = new Ducky();

ducky.addTask({
  name: "Weekly Contributors",
  description:
    "Analyzes top contributors and airdrops DUCKAI tokens to winners",
  cronPattern: "0 0 * * 1", // Every Monday at midnight
  task: async () => {
    // Use ducky's internal test mode flag
    const isTestMode =
      process.argv.includes("--test") || process.argv.includes("-t");
    console.log(
      `🦆 Running contributor rewards in ${
        isTestMode ? "test" : "production"
      } mode`
    );
    await contributorMain(isTestMode);
  },
});

// Start all tasks
ducky.start();
