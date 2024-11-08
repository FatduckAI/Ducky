import type { Server } from "bun";
import { CronJob } from "cron";
import { db } from "../../db";
import { duckyAi } from "../../db/schema";
import type { AgentTask } from "./types";

export class Agent {
  private name: string;
  private tasks: Map<string, CronJob>;
  private isTestMode: boolean;
  private server: Server | null = null;

  constructor(config: { name: string; isTestMode?: boolean }) {
    this.name = config.name;
    this.tasks = new Map();
    this.isTestMode = config.isTestMode ?? true;
  }

  private async logToDatabase(message: string, speaker = "System") {
    if (!this.isTestMode) {
      await db.insert(duckyAi).values({
        content: message,
        timestamp: new Date().toISOString(),
        speaker,
        posted: false,
      });
    } else {
      console.log("TEST MODE - Would log to DB:", { message, speaker });
    }
  }

  public async runTask(task: AgentTask): Promise<string> {
    try {
      const prompt = await task.prompt();
      // Skip empty prompts (like when no new PR is found)
      if (!prompt) {
        return "";
      }
      // if no ai needed just run the task
      if (!task.ai) {
        const response = await task.prompt();
        return response;
      }
      // Get AI response using task's provider
      const response = await task.provider.generateResponse(
        prompt,
        task.systemPrompt
      );

      if (!this.isTestMode && task.production) {
        const deliveryResponse = await task.delivery.send(response);
        // run the callback if it exists
        if (task.onComplete) {
          await task.onComplete(response, deliveryResponse);
        }
        return deliveryResponse;
      } else {
        console.log(
          `🤖 TEST MODE - Would send via ${task.delivery.type}:`,
          response
        );
        if (task.onComplete) {
          await task.onComplete(response, "test-id");
        }
        return "test-id";
      }
    } catch (error) {
      console.error(`Error in agent ${this.name}:`, error);
      await this.logToDatabase(
        `Error in task ${task.name}: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
      throw error;
    }
  }

  public async addTask(task: AgentTask): Promise<boolean> {
    try {
      // Comment out for testing
      if (this.isTestMode) {
        await this.runTask(task);
        return true;
      }

      if (task.cronPattern) {
        const job = new CronJob(task.cronPattern, async () => {
          try {
            await this.runTask(task);
          } catch (error) {
            console.error(`Error in task ${task.name}:`, error);
          }
        });

        this.tasks.set(task.name, job);

        job.start();
      }

      console.log(
        `🤖 Added task: ${task.name}${
          task.cronPattern ? ` (${task.cronPattern})` : ""
        }`
      );
      return true;
    } catch (error) {
      console.error(`Error adding task ${task.name}:`, error);
      return false;
    }
  }

  public startServer(port: number = 3000): void {
    const agent = this;

    this.server = Bun.serve({
      port,
      async fetch(req) {
        const url = new URL(req.url);

        if (url.pathname === "/health" && req.method === "GET") {
          return new Response(JSON.stringify({ status: "healthy" }), {
            headers: { "Content-Type": "application/json" },
          });
        }

        if (url.pathname === "/agent/run" && req.method === "POST") {
          try {
            const body = await req.json();
            if (!body.task) {
              return new Response(
                JSON.stringify({ error: "Task configuration is required" }),
                {
                  status: 400,
                  headers: { "Content-Type": "application/json" },
                }
              );
            }

            const response = await agent.runTask(body.task);
            return new Response(JSON.stringify({ response }), {
              headers: { "Content-Type": "application/json" },
            });
          } catch (error) {
            return new Response(
              JSON.stringify({
                error: error instanceof Error ? error.message : "Unknown error",
              }),
              {
                status: 500,
                headers: { "Content-Type": "application/json" },
              }
            );
          }
        }

        if (url.pathname === "/tasks/status" && req.method === "GET") {
          const status = Array.from(agent.tasks.entries()).map(
            ([name, job]) => ({
              name,
              running: job.running,
              nextDate: job.nextDate(),
            })
          );

          return new Response(JSON.stringify({ tasks: status }), {
            headers: { "Content-Type": "application/json" },
          });
        }

        return new Response("Not Found", { status: 404 });
      },
    });

    console.log(`🤖 Agent server listening on port ${port}`);
  }

  public startAll(): void {
    if (this.isTestMode) {
      console.log("TEST MODE - Would start all tasks");
      return;
    }

    this.tasks.forEach((task, name) => {
      task.start();
      console.log(`🤖 Started task: ${name}`);
    });
  }

  public stopAll(): void {
    this.tasks.forEach((task, name) => {
      task.stop();
      console.log(`🤖 Stopped task: ${name}`);
    });

    if (this.server) {
      this.server.stop();
      console.log("🤖 Stopped server");
    }
  }
}
