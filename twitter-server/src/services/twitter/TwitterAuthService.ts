// src/services/twitter/TwitterAuthService.ts
import { Scraper } from "agent-twitter-client";
import type { CookieJSON } from "../../../types";
import { BaseService } from "../base/BaseService";

export class TwitterAuthService extends BaseService {
  private scraper: Scraper;
  private cookiesPath: string;
  private loginRetryAttempts = 0;
  private readonly MAX_LOGIN_RETRIES = 3;

  constructor(scraper: Scraper, cookiesPath?: string) {
    super();
    this.scraper = scraper;
    this.cookiesPath =
      cookiesPath || process.env.COOKIES_PATH || "cookies.json";
  }

  private async loadCookies(): Promise<string[]> {
    try {
      const cookiesJson = JSON.parse(await Bun.file(this.cookiesPath).text());
      return cookiesJson.map((cookieJson: CookieJSON) => {
        const parts = [
          `${cookieJson.key}=${cookieJson.value}`,
          `Domain=${cookieJson.domain || ".twitter.com"}`,
          `Path=${cookieJson.path || "/"}`,
        ];

        if (cookieJson.secure) parts.push("Secure");
        if (cookieJson.httpOnly) parts.push("HttpOnly");
        if (cookieJson.sameSite) parts.push(`SameSite=${cookieJson.sameSite}`);
        if (cookieJson.expires) parts.push(`Expires=${cookieJson.expires}`);

        return parts.join("; ");
      });
    } catch (error) {
      this.logError("Could not load cookies", error);
      return [];
    }
  }

  private async saveCookies(): Promise<void> {
    try {
      const cookies = await this.scraper.getCookies();
      await Bun.write(this.cookiesPath, JSON.stringify(cookies, null, 2));
    } catch (error) {
      this.logError("Error saving cookies", error);
      throw error;
    }
  }

  private async attemptLogin(): Promise<boolean> {
    if (!process.env.TWITTER_USERNAME || !process.env.TWITTER_PASSWORD) {
      throw new Error("Missing Twitter credentials");
    }

    await this.scraper.login(
      process.env.TWITTER_USERNAME,
      process.env.TWITTER_PASSWORD,
      process.env.TWITTER_EMAIL,
      process.env.TWITTER_2FA_SECRET
    );

    const isLoggedIn = await this.scraper.isLoggedIn();
    if (isLoggedIn) {
      await this.saveCookies();
      this.loginRetryAttempts = 0;
    }
    return isLoggedIn;
  }

  async initialize(): Promise<void> {
    try {
      const cookies = await this.loadCookies();
      if (cookies.length > 0) {
        await this.scraper.setCookies(cookies);

        if (await this.scraper.isLoggedIn()) {
          this.logDebug("Successfully initialized with cookies");
          return;
        }
      }

      if (await this.attemptLogin()) {
        this.logDebug("Successfully initialized with login");
        return;
      }

      throw new Error("Failed to login with both cookies and credentials");
    } catch (error) {
      this.logError("Error initializing Twitter service", error);
      await this.logToDatabase(
        `Error initializing Twitter service: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
      throw error;
    }
  }

  async ensureLoggedIn(): Promise<void> {
    if (!(await this.scraper.isLoggedIn())) {
      if (this.loginRetryAttempts >= this.MAX_LOGIN_RETRIES) {
        throw new Error("Maximum login retry attempts reached");
      }
      this.loginRetryAttempts++;
      await this.initialize();
    }
  }
}
