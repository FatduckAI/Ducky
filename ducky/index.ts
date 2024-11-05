import { Ducky } from "./src/ducky";
import { main as contributorMain } from "./src/services/contributions/contributor";

// Create Ducky instance
const ducky = new Ducky();

ducky.addTask({
  name: "Weekly Contributors",
  cronPattern: "0 0 * * 1", // Every Monday at midnight
  task: contributorMain,
});

// Start all tasks
ducky.start();
