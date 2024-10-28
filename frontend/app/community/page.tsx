"use client";
import DailyTrendsChart from "@/components/DailyTrendChart";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ChartConfig, ChartContainer } from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface SentimentQueryParams {
  days?: number;
  minMessages?: number;
}

const useSentimentData = ({
  days = 30,
  minMessages = 10,
}: SentimentQueryParams = {}) => {
  const { data: dailyTrends, isLoading: isDailyLoading } = useQuery({
    queryKey: ["dailyTrends", days],
    queryFn: async () => {
      const res = await fetch(`/api/sentiment/daily_trends?days=${days}`);
      return res.json();
    },
  });

  const { data: hourlyPattern, isLoading: isHourlyLoading } = useQuery({
    queryKey: ["hourlyPattern"],
    queryFn: async () => {
      const res = await fetch("/api/sentiment/hourly_pattern");
      return res.json();
    },
  });

  const { data: userAnalysis, isLoading: isUserLoading } = useQuery({
    queryKey: ["userAnalysis", minMessages],
    queryFn: async () => {
      const res = await fetch(
        `/api/sentiment/user_analysis?min_messages=${minMessages}`
      );
      return res.json();
    },
  });

  const { data: stats, isLoading: isStatsLoading } = useQuery({
    queryKey: ["sentimentStats", days],
    queryFn: async () => {
      const res = await fetch(`/api/sentiment/stats?days=${days}`);
      return res.json();
    },
  });

  return {
    dailyTrends,
    hourlyPattern,
    userAnalysis,
    stats,
    isLoading:
      isDailyLoading || isHourlyLoading || isUserLoading || isStatsLoading,
  };
};

const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-64">
    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
  </div>
);

const ErrorAlert = ({ message }: { message: string }) => (
  <Alert variant="destructive" className="mb-4">
    <AlertDescription>{message}</AlertDescription>
  </Alert>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border rounded-lg shadow-lg p-4">
        <p className="text-sm font-medium">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value.toFixed(3)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

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

export default function Dashboard() {
  const [timeRange, setTimeRange] = React.useState("30");
  const [minMessages, setMinMessages] = React.useState("10");

  const { dailyTrends, hourlyPattern, userAnalysis, stats, isLoading } =
    useSentimentData({
      days: parseInt(timeRange),
      minMessages: parseInt(minMessages),
    });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Community Dashboard</h1>
          <p className="text-muted-foreground">
            Ducky&apos;s sentiment analysis and user activity
          </p>
        </div>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select time range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="space-y-8">
          {/* Stats Overview */}
          {stats && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader>
                  <CardTitle>Total Messages</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{stats.total_messages}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Average Sentiment</CardTitle>
                </CardHeader>
                <CardContent>
                  <p
                    className="text-2xl font-bold"
                    style={{
                      color:
                        stats.avg_sentiment_balance > 0 ? "#22c55e" : "#ef4444",
                    }}
                  >
                    {stats.avg_sentiment_balance?.toFixed(3)}
                  </p>
                </CardContent>
              </Card>
              {/* Add more stat cards as needed */}
            </div>
          )}

          <Tabs defaultValue="daily" className="space-y-4">
            <TabsList>
              <TabsTrigger value="daily">Daily Trends</TabsTrigger>
              <TabsTrigger value="hourly">Hourly Patterns</TabsTrigger>
              <TabsTrigger value="users">User Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="daily">
              <DailyTrendsChart />
            </TabsContent>

            <TabsContent value="hourly">
              <Card>
                <CardHeader>
                  <CardTitle>Hourly Activity Pattern</CardTitle>
                  <CardDescription>
                    Message distribution across hours
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[400px]">
                  <ChartContainer config={chartConfig}>
                    <BarChart data={hourlyPattern} width={1000} height={400}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        className="stroke-muted"
                      />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Bar dataKey="message_count" fill="#3b82f6" />
                    </BarChart>
                  </ChartContainer>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="users">
              <Card>
                <CardHeader>
                  <CardTitle>User Sentiment Analysis</CardTitle>
                  <CardDescription>
                    Top users by sentiment and activity
                  </CardDescription>
                  <Select value={minMessages} onValueChange={setMinMessages}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Minimum messages" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">Min 5 messages</SelectItem>
                      <SelectItem value="10">Min 10 messages</SelectItem>
                      <SelectItem value="20">Min 20 messages</SelectItem>
                    </SelectContent>
                  </Select>
                </CardHeader>
                <CardContent className="h-[400px]">
                  <ChartContainer config={chartConfig}>
                    <BarChart
                      data={userAnalysis}
                      layout="vertical"
                      width={1000}
                      height={400}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        className="stroke-muted"
                      />
                      <XAxis type="number" />
                      <YAxis dataKey="username" type="category" width={100} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Bar dataKey="positive" fill="#22c55e" stackId="stack" />
                    </BarChart>
                  </ChartContainer>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
