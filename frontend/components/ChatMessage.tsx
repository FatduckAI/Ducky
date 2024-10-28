"use client";

import dayjs from "@/lib/dayjs";
import type { ChatMessage } from "@/types/chat";
import { useState } from "react";

interface ChatMessageProps {
  message: ChatMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const CHARACTER_LIMIT = 250;
  const shouldTruncate = message.content.length > CHARACTER_LIMIT;
  const displayContent =
    shouldTruncate && !isExpanded
      ? message.content.slice(0, CHARACTER_LIMIT)
      : message.content;

  const getSpeakerStyle = () => {
    const speakerLower = message.speaker.toLowerCase();
    switch (speakerLower) {
      case "ducky":
        return "font-bold bg-zinc-50";
      case "cleo":
        return "";
      case "error":
        return "text-red-600 bg-red-50";
      default:
        return "text-muted-foreground text-sm";
    }
  };

  const messageTime = dayjs(message.timestamp);
  const timeAgo = messageTime.fromNow();
  const fullTime = messageTime.format("MMM D, YYYY h:mm A");

  return (
    <div className="flex gap-6 items-start pl-2 mb-2">
      <div className="text-xs text-ducky-text mt-2 hidden md:block">
        <span title={fullTime}>{timeAgo}</span>
      </div>
      <div className="min-w-0 max-w-6xl flex-1">
        <div className={`rounded p-1 ${getSpeakerStyle()}`}>
          <div className="pl-2 flex flex-row gap-4">
            <div className="font-bold text-sm mb-2 flex-1">
              [{message.speaker}]
            </div>
            <div className="flex-grow">
              <span className="message-content text-gray-600">
                {displayContent}
              </span>
              {shouldTruncate && (
                <button
                  className="text-ducky-text hover:underline ml-2"
                  onClick={() => setIsExpanded(!isExpanded)}
                >
                  {isExpanded ? "show less" : "..."}
                </button>
              )}
            </div>
            <div className="text-xs text-ducky-text mt-2 block md:hidden">
              <span title={fullTime}>{timeAgo}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
