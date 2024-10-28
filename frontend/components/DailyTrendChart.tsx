"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ChartConfig, ChartContainer } from "@/components/ui/chart";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border rounded-lg shadow-lg p-4">
        <p className="text-sm font-medium mb-2">{label}</p>
        {payload.map((entry: any) => (
          <p
            key={entry.name}
            className="text-sm"
            style={{ color: entry.color }}
          >
            {`${entry.name}: ${entry.value.toFixed(3)}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function DailyTrendsChart() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dailyTrends"],
    queryFn: async () => {
      const response = await fetch("/api/sentiment/daily_trends");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      if (!Array.isArray(data)) {
        console.error("Data is not an array:", data);
        throw new Error("Invalid data format");
      }

      const formattedData = data
        .map((item: any) => {
          if (typeof item !== "object" || item === null) {
            console.error("Invalid item in data:", item);
            return null;
          }
          const date = new Date(item.date);
          return {
            ...item,
            date: date.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric", // Add year to differentiate between years
            }),
            originalDate: item.date, // Keep the original date for sorting
            positive: Number(item.positive),
            negative: Number(item.negative),
            helpful: Number(item.helpful),
            sarcastic: Number(item.sarcastic),
            message_count: Number(item.message_count),
          };
        })
        .filter(Boolean);

      // Sort the data by the original date
      formattedData.sort(
        (a, b) =>
          new Date(a.originalDate).getTime() -
          new Date(b.originalDate).getTime()
      );

      return formattedData;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    console.error("Error fetching data:", error);
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load daily trends data: {(error as Error).message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Alert>
        <AlertDescription>
          No data available for the selected period
        </AlertDescription>
      </Alert>
    );
  }

  const totalMessages = data.reduce(
    (sum: number, day: any) => sum + day.message_count,
    0
  );

  const chartConfig = {
    desktop: {
      label: "Desktop",
      color: "#2563eb",
    },
    mobile: {
      label: "Mobile",
      color: "#60a5fa",
    },
  } satisfies ChartConfig;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Daily Sentiment Trends</CardTitle>
        <CardDescription>
          Tracking {data.length} days of sentiment data (Total Messages:{" "}
          {totalMessages.toLocaleString()})
        </CardDescription>
      </CardHeader>
      <CardContent className="h-full w-full">
        <ChartContainer
          config={chartConfig}
          className="h-[400px] min-h-[400px] w-full"
        >
          <LineChart
            accessibilityLayer
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            width={1000}
            height={400}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-muted"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={{ fill: "currentColor", fontSize: 12 }}
              tickMargin={10}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 1]}
              tickCount={6}
              tick={{ fill: "currentColor", fontSize: 12 }}
              tickFormatter={(value) => value.toFixed(1)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} />
            <Line
              name="Positive"
              type="monotone"
              dataKey="positive"
              stroke="hsl(var(--chart-1))"
              strokeWidth={2}
              dot={{ r: 4, strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
            <Line
              name="Negative"
              type="monotone"
              dataKey="negative"
              stroke="hsl(var(--chart-2))"
              strokeWidth={2}
              dot={{ r: 4, strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
            <Line
              name="Helpful"
              type="monotone"
              dataKey="helpful"
              stroke="hsl(var(--chart-3))"
              strokeWidth={2}
              dot={{ r: 4, strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
            <Line
              name="Sarcastic"
              type="monotone"
              dataKey="sarcastic"
              stroke="hsl(var(--chart-4))"
              strokeWidth={2}
              dot={{ r: 4, strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
