// src/services/base/RateLimitService.ts
export class RateLimitService {
  protected count: number = 0;
  protected lastOperationTime: number = 0;
  private minDelay: number;
  private maxOperationsPerWindow: number;
  private windowDuration: number;

  constructor(
    minDelay: number,
    maxOperationsPerWindow: number,
    windowDuration: number = 15 * 60 * 1000
  ) {
    this.minDelay = minDelay;
    this.maxOperationsPerWindow = maxOperationsPerWindow;
    this.windowDuration = windowDuration;
  }

  async respectRateLimit(): Promise<void> {
    const now = Date.now();

    // Ensure minimum delay between operations
    const timeSinceLastOperation = now - this.lastOperationTime;
    if (timeSinceLastOperation < this.minDelay) {
      await new Promise((resolve) =>
        setTimeout(resolve, this.minDelay - timeSinceLastOperation)
      );
    }

    // Reset count if window has passed
    if (now - this.lastOperationTime > this.windowDuration) {
      this.count = 0;
    }

    // Check if we're approaching limits
    if (this.count >= this.maxOperationsPerWindow) {
      const waitTime = this.windowDuration - (now - this.lastOperationTime);
      await new Promise((resolve) => setTimeout(resolve, waitTime));
      this.count = 0;
    }

    this.count++;
    this.lastOperationTime = now;
  }

  getStatus(): {
    count: number;
    remaining: number;
    canOperate: boolean;
    waitTime: number;
  } {
    const now = Date.now();
    const timeInWindow =
      now - Math.max(this.lastOperationTime, now - this.windowDuration);
    const remaining =
      this.maxOperationsPerWindow -
      (timeInWindow < this.windowDuration ? this.count : 0);
    const waitTime = Math.max(
      0,
      this.minDelay - (now - this.lastOperationTime)
    );

    return {
      count: this.count,
      remaining,
      canOperate: remaining > 0 && waitTime === 0,
      waitTime,
    };
  }

  reset(): void {
    this.count = 0;
    this.lastOperationTime = 0;
  }
}
