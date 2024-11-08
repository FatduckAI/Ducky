CREATE TABLE IF NOT EXISTS "github_pr_analysis" (
	"id" serial PRIMARY KEY NOT NULL,
	"pr_number" integer NOT NULL,
	"pr_title" text NOT NULL,
	"pr_author" text NOT NULL,
	"repo_owner" text NOT NULL,
	"repo_name" text NOT NULL,
	"merge_sha" text NOT NULL,
	"analysis" text NOT NULL,
	"file_count" integer NOT NULL,
	"additions" integer NOT NULL,
	"deletions" integer NOT NULL,
	"posted" boolean DEFAULT false NOT NULL,
	"tweet_id" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
