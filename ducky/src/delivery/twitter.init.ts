import { Scraper } from "agent-twitter-client";

interface CookieJSON {
  key: string;
  value: string;
  domain?: string;
  path?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: string;
  expires?: string;
}

export class ServiceInitializer {
  private static scraper: Scraper | null = null;

  private static async loadCookies(): Promise<string[]> {
    try {
      const cookiesEnv = process.env.TWITTER_COOKIES;
      if (!cookiesEnv) {
        console.log("No cookies found in environment variables");
        return [];
      }

      const cookiesJson: CookieJSON[] = JSON.parse(cookiesEnv);
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
      console.error("Could not load cookies:", error);
      return [];
    }
  }

  private static async saveCookies(scraper: Scraper) {
    try {
      const cookies = await scraper.getCookies();
      await Bun.write("cookies.json", JSON.stringify(cookies, null, 2));
    } catch (error) {
      console.error("Error saving cookies:", error);
    }
  }

  private static async loginToTwitter(scraper: Scraper): Promise<boolean> {
    if (!process.env.TWITTER_USERNAME || !process.env.TWITTER_PASSWORD) {
      throw new Error("Missing Twitter credentials");
    }

    await scraper.login(
      process.env.TWITTER_USERNAME,
      process.env.TWITTER_PASSWORD,
      process.env.TWITTER_EMAIL,
      process.env.TWITTER_2FA_SECRET
    );

    const isLoggedIn = await scraper.isLoggedIn();
    if (isLoggedIn) {
      await this.saveCookies(scraper);
    }
    return isLoggedIn;
  }

  public static async initialize(): Promise<Scraper> {
    if (this.scraper) {
      return this.scraper;
    }

    this.scraper = new Scraper();
    const cookies = await this.loadCookies();

    if (cookies.length > 0) {
      await this.scraper.setCookies(cookies);
      if (await this.scraper.isLoggedIn()) {
        console.log("Successfully initialized Twitter with cookies");
        return this.scraper;
      }
    }

    if (await this.loginToTwitter(this.scraper)) {
      console.log("Successfully initialized Twitter with login");
      return this.scraper;
    }

    throw new Error("Failed to initialize Twitter service");
  }
}
