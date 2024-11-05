ALTER TABLE "telegram_messages" ADD PRIMARY KEY ("message_id");--> statement-breakpoint
ALTER TABLE "telegram_messages" ALTER COLUMN "message_id" SET NOT NULL;