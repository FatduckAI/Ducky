import { db } from "../../../db";
import { duckyAi } from "../../../db/schema";

export class BaseService {
  protected logDebug(message: string, data?: any) {
    console.log(`[${this.constructor.name}] ${message}`);
    if (data) {
      console.log(JSON.stringify(data, null, 2));
    }
  }

  protected logError(message: string, error: any) {
    console.error(`[${this.constructor.name} Error] ${message}`);
    console.error("Error details:", {
      name: error?.name,
      message: error?.message,
      status: error?.response?.status,
      headers: error?.response?.headers,
      data: error?.response?.data,
    });
  }

  protected async logToDatabase(message: string, speaker = "System") {
    try {
      await db.insert(duckyAi).values({
        content: message,
        timestamp: new Date().toISOString(),
        speaker,
        posted: false,
      });
    } catch (error) {
      this.logError("Error logging to database", error);
    }
  }
}
