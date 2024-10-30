"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import type { ChatMessage } from "../types/chat";

export function useChat() {
  const queryClient = useQueryClient();

  const {
    data: messages = [],
    isLoading,
    isError,
    error,
  } = useQuery<ChatMessage[]>({
    queryKey: ["chat-history"],
    queryFn: async () => {
      const response = await fetch("/api/chat_history");
      const data = await response.json();
      return data.messages;
    },
    select: (data) => {
      // Sort messages by timestamp
      return [...data].sort(
        (a, b) => dayjs(a.timestamp).valueOf() - dayjs(b.timestamp).valueOf()
      );
    },
    retry: 3, // Will retry failed requests 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  });

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-history"] });
    },
  });

  return {
    messages,
    isLoading,
    isError,
    error,
    sendMessage,
  };
}
