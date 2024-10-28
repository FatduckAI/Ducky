"use client";

import { useChat } from "@/hooks/useChat";
import { useEffect, useRef } from "react";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";

export function ChatContainer() {
  const { messages, isLoading, isError, error } = useChat();
  const containerRef = useRef<HTMLDivElement>(null);
  const isInitialLoad = useRef(true);

  const scrollToBottom = (instant: boolean = false) => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  // Initial load - instant scroll
  useEffect(() => {
    if (messages.length > 0 && isInitialLoad.current) {
      scrollToBottom(true);
      isInitialLoad.current = false;
    }
  }, [messages]);

  // New messages - smooth scroll
  useEffect(() => {
    if (!isInitialLoad.current && messages.length > 0) {
      if (containerRef.current) {
        containerRef.current.scrollTo({
          top: containerRef.current.scrollHeight,
          behavior: "smooth",
        });
      }
    }
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-250px)]">
        <div className="animate-pulse text-ducky-text">Loading messages...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-250px)]">
        <div className="text-red-500">
          Error loading messages:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8 mx-auto md:p-0">
      <div className="transition-all duration-300 px-16">
        <div
          ref={containerRef}
          className="border border-ducky-border rounded h-[calc(100vh-250px)] overflow-y-auto mb-4"
        >
          {messages.map((message, index) => (
            <ChatMessage
              key={`${message.conversation_id}-${index}`}
              message={message}
            />
          ))}
        </div>
        <ChatInput onSend={() => scrollToBottom(false)} />
        <div className="text-center text-red-700">
          Chating with Ducky will be available soon, you can access, Mistral,
          GPT-4o, Claude, Llama3.1, Gemini and Mallard (who ducky is based off
          of) at&nbsp;
          <a href="https://fatduck.ai" className="text-red-700 hover:underline">
            https://fatduck.ai
          </a>
          &nbsp;Use code "Ducky" for 50% off
        </div>
      </div>
    </div>
  );
}
