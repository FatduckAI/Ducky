import type { DeliverySystem } from "../agent/types";

export class ConsoleDeliveryService implements DeliverySystem {
  type: "console" = "console";
  send: (content: string) => Promise<string> = async (content) => content;
}
