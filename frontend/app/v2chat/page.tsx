"use client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Conversation } from "@/lib/sdk";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { Loader2, Send } from "lucide-react";
import React from "react";

const DEFAULT_USER_ID = "12344444";

interface MessageResponse {
  messages: Array<{
    id: string;
    userId: string;
    content: string;
    role: "user" | "assistant";
    timestamp: number;
  }>;
  hasMore: boolean;
  nextCursor?: string;
}

const ConversationsPage = () => {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const [selectedConversation, setSelectedConversation] =
    React.useState<Conversation | null>(null);
  const [page, setPage] = React.useState(0);
  const [includeInactive, setIncludeInactive] = React.useState(false);
  const [messageInput, setMessageInput] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [userId] = React.useState(DEFAULT_USER_ID);

  // Query for conversations list
  const {
    data: conversationsData,
    isLoading: isLoadingConversations,
    isError: isConversationsError,
    error: conversationsError,
    refetch: refetchConversations,
  } = useQuery({
    queryKey: ["conversations", page, includeInactive, userId],
    queryFn: async () => {
      const response = await fetch(
        `/api/conversation?${new URLSearchParams({
          user_id: userId,
          page: String(page),
          include_inactive: String(includeInactive),
          page_size: "10",
        })}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch conversations");
      }
      const data = await response.json();
      return data as {
        conversations: Conversation[];
        totalCount: number;
        hasMore: boolean;
      };
    },
  });

  // Query for conversation messages with debug logging
  const {
    data: messagesData,
    isLoading: isLoadingMessages,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch: refetchMessages,
  } = useInfiniteQuery<MessageResponse>({
    // Add to your useInfiniteQuery error handling:
    queryKey: ["conversation-messages", selectedConversation?.id],
    initialPageParam: undefined,
    queryFn: async ({ pageParam }) => {
      if (!selectedConversation?.id) {
        console.log("No conversation selected, skipping query");
        throw new Error("No conversation selected");
      }

      const params = new URLSearchParams();
      if (typeof pageParam === "string") {
        params.set("offset", pageParam);
      }
      params.set("limit", "50");

      const url = `/api/conversation/${selectedConversation.id}/messages?${params}`;
      console.log("Fetching messages from:", url);

      try {
        const response = await fetch(url);
        console.log("Response status:", response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error("Error response:", errorText);
          throw new Error(
            `Failed to fetch messages: ${response.status} ${errorText}`
          );
        }

        const data = await response.json();
        console.log("Received messages data:", data);
        return data;
      } catch (error) {
        console.error("Error in message query:", error);
        throw error;
      }
    },
    getNextPageParam: (lastPage) => {
      console.log("Getting next page param:", lastPage.nextCursor);
      return lastPage.nextCursor;
    },
    enabled: !!selectedConversation?.id,
  });

  // Handle conversation selection with debug logging
  const handleConversationSelect = async (conversation: Conversation) => {
    console.log("Selected conversation:", conversation);
    setSelectedConversation(conversation);
    setError(null);
  };

  // Auto-scroll to bottom when messages update
  React.useEffect(() => {
    if (messagesData?.pages) {
      scrollToBottom();
    }
  }, [messagesData]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Handle message sending
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConversation || !messageInput.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          userId,
          platform: selectedConversation.platform,
          content: messageInput.trim(),
          priority: "normal",
          conversationId: selectedConversation.id,
          metadata: {},
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      await response.json();

      // Refetch both conversations and messages to get the latest data
      await Promise.all([refetchConversations(), refetchMessages()]);

      setMessageInput("");
      scrollToBottom();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-full">
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel defaultSize={30} minSize={20}>
          <Card className="h-full rounded-none border-0">
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Conversations</h2>
              <Select
                value={includeInactive ? "all" : "active"}
                onValueChange={(value) => setIncludeInactive(value === "all")}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Filter" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active Only</SelectItem>
                  <SelectItem value="all">All</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {isLoadingConversations ? (
              <div className="flex justify-center items-center h-64">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : isConversationsError ? (
              <div className="p-4 text-red-500">
                Error:{" "}
                {conversationsError instanceof Error
                  ? conversationsError.message
                  : "Failed to load conversations"}
              </div>
            ) : (
              <div className="overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Platform</TableHead>
                      <TableHead>Started</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversationsData?.conversations.map((conversation) => (
                      <TableRow
                        key={conversation.id}
                        className={`cursor-pointer hover:bg-gray-100 ${
                          selectedConversation?.id === conversation.id
                            ? "bg-gray-100"
                            : ""
                        }`}
                        onClick={() => handleConversationSelect(conversation)}
                      >
                        <TableCell>{conversation.platform}</TableCell>
                        <TableCell>
                          {dayjs(conversation.createdAt).format(
                            "MMM D, YYYY h:mm A"
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              conversation.isActive ? "default" : "secondary"
                            }
                          >
                            {conversation.isActive ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            <div className="p-4 border-t mt-auto">
              <div className="flex justify-between items-center">
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-500">
                  Page {page + 1} of{" "}
                  {Math.ceil((conversationsData?.totalCount ?? 0) / 10)}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!conversationsData?.hasMore}
                >
                  Next
                </Button>
              </div>
            </div>
          </Card>
        </ResizablePanel>

        <ResizableHandle />

        <ResizablePanel defaultSize={70}>
          {selectedConversation ? (
            <div className="h-full flex flex-col">
              <div className="p-4 border-b">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-lg font-semibold">
                      Conversation with {selectedConversation.userId}
                    </h2>
                    <p className="text-sm text-gray-500">
                      {selectedConversation.platform} ·{" "}
                      {dayjs(selectedConversation.createdAt).format(
                        "MMM D, YYYY h:mm A"
                      )}
                    </p>
                  </div>
                  <Badge
                    variant={
                      selectedConversation.isActive ? "default" : "secondary"
                    }
                  >
                    {selectedConversation.isActive ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {isLoadingMessages ? (
                  <div className="flex justify-center items-center h-full">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <>
                    {messagesData?.pages.map((page, i) => (
                      <React.Fragment key={i}>
                        {page.messages.map((message) => (
                          <div
                            key={message.id}
                            className={`p-3 rounded-lg ${
                              message.role === "assistant"
                                ? "bg-blue-100 ml-8"
                                : "bg-gray-100 mr-8"
                            }`}
                          >
                            <div className="flex justify-between items-start">
                              <div className="font-medium text-gray-700">
                                {message.role === "assistant"
                                  ? "Assistant"
                                  : "User"}
                              </div>
                              <div className="text-sm text-gray-500">
                                {dayjs(message.timestamp).format(
                                  "MMM D, YYYY h:mm A"
                                )}
                              </div>
                            </div>
                            <div className="mt-1 whitespace-pre-wrap">
                              {message.content}
                            </div>
                          </div>
                        ))}
                      </React.Fragment>
                    ))}
                    {hasNextPage && (
                      <div className="flex justify-center py-2">
                        <Button
                          variant="outline"
                          onClick={() => fetchNextPage()}
                          disabled={isFetchingNextPage}
                        >
                          {isFetchingNextPage ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            "Load More"
                          )}
                        </Button>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {error && (
                <div className="p-3 mx-4 mb-4 rounded bg-red-100 text-red-700">
                  {error}
                </div>
              )}

              <form onSubmit={handleSendMessage} className="p-4 border-t">
                <div className="flex gap-4">
                  <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 p-2 border rounded focus:ring-2 focus:ring-blue-500"
                    disabled={!selectedConversation.isActive || isLoading}
                  />
                  <Button
                    type="submit"
                    disabled={
                      !selectedConversation.isActive ||
                      isLoading ||
                      !messageInput.trim()
                    }
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </form>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              Select a conversation to start chatting
            </div>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

export default ConversationsPage;
