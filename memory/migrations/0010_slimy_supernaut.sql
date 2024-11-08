CREATE TABLE IF NOT EXISTS "btc_price_data" (
	"id" serial PRIMARY KEY NOT NULL,
	"timestamp" timestamp DEFAULT now(),
	"current_price" integer,
	"price_change_7d" integer
);
