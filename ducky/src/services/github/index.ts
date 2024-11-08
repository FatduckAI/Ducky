import { db } from "@/db";
import { githubPRAnalysis } from "@/db/schema";
import { Octokit } from "@octokit/rest";
import { and, eq } from "drizzle-orm";
import { ducky, generatePrompt } from "../../ducky/character";
import type { PRDetails } from "./types";

class GitHubService {
  private octokit: Octokit;
  private currentPRDetails: PRDetails | null = null;

  constructor(githubToken: string) {
    this.octokit = new Octokit({ auth: githubToken });
  }

  private async getPRDetails(
    owner: string,
    repo: string,
    pullNumber: number
  ): Promise<PRDetails> {
    const [pr, files] = await Promise.all([
      this.octokit.pulls.get({
        owner,
        repo,
        pull_number: pullNumber,
      }),
      this.octokit.pulls.listFiles({
        owner,
        repo,
        pull_number: pullNumber,
      }),
    ]);

    return {
      number: pullNumber,
      title: pr.data.title,
      description: pr.data.body || "",
      author: pr.data.user?.login || "Unknown",
      baseBranch: pr.data.base.ref,
      mergeSha: pr.data.merge_commit_sha,
      fileCount: files.data.length,
      additions: files.data.reduce((sum, file) => sum + file.additions, 0),
      deletions: files.data.reduce((sum, file) => sum + file.deletions, 0),
      files: files.data.map((file) => ({
        filename: file.filename,
        status: file.status,
        additions: file.additions,
        deletions: file.deletions,
        patch: file.patch || "",
      })),
    };
  }

  private async getMostRecentMergedPR(
    owner: string,
    repo: string
  ): Promise<PRDetails> {
    const { data: prs } = await this.octokit.pulls.list({
      owner,
      repo,
      state: "closed",
      sort: "updated",
      direction: "desc",
      per_page: 1,
      base: "master",
    });

    if (prs.length === 0 || !prs[0].merged_at) {
      throw new Error("No merged PRs found");
    }

    return this.getPRDetails(owner, repo, prs[0].number);
  }

  private async checkPRAnalysisExists(
    prNumber: number,
    repoOwner: string,
    repoName: string
  ): Promise<boolean> {
    const existing = await db
      .select({ id: githubPRAnalysis.id })
      .from(githubPRAnalysis)
      .where(
        and(
          eq(githubPRAnalysis.prNumber, prNumber),
          eq(githubPRAnalysis.repoOwner, repoOwner),
          eq(githubPRAnalysis.repoName, repoName)
        )
      )
      .limit(1);

    return existing.length > 0;
  }

  public async savePRAnalysis(analysis: string, tweetId: string) {
    if (!this.currentPRDetails) {
      console.log("No PR details available for saving analysis");
      return;
    }

    await db.insert(githubPRAnalysis).values({
      prNumber: this.currentPRDetails.number,
      prTitle: this.currentPRDetails.title,
      prAuthor: this.currentPRDetails.author,
      repoOwner: ducky.github.owner,
      repoName: ducky.github.repo,
      mergeSha: this.currentPRDetails.mergeSha || "",
      analysis,
      fileCount: this.currentPRDetails.fileCount,
      additions: this.currentPRDetails.additions,
      deletions: this.currentPRDetails.deletions,
      tweetId,
      posted: true,
    });

    // Clear the current PR details after saving
    this.currentPRDetails = null;
  }

  public async getNextPRAnalysis() {
    try {
      const prDetails = await this.getMostRecentMergedPR(
        ducky.github.owner,
        ducky.github.repo
      );

      const exists = await this.checkPRAnalysisExists(
        prDetails.number,
        ducky.github.owner,
        ducky.github.repo
      );

      if (exists) {
        console.log(`🤖 PR #${prDetails.number} already analyzed, skipping`);
        return { prompt: "" };
      }

      // Store the PR details for use in savePRAnalysis
      this.currentPRDetails = prDetails;
      return { prompt: generatePrompt.forPRAnalysis(prDetails) };
    } catch (error) {
      if (error instanceof Error && error.message === "No merged PRs found") {
        console.log("🤖 No new merged PRs to analyze");
        return { prompt: "" };
      }
      throw error;
    }
  }
}

export const createGitHubService = (githubToken: string) => {
  return new GitHubService(githubToken);
};
