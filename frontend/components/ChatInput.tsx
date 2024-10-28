"use client";

import { useChat } from "@/hooks/useChat";
import { useState } from "react";

interface ChatInputProps {
  onSend?: () => void;
}

export function ChatInput({ onSend }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const { sendMessage } = useChat();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    try {
      await sendMessage.mutateAsync(message);
      setMessage("");
      onSend?.();
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        className="flex-grow border border-ducky-border p-2"
        placeholder="Chat will be generally available soon"
        disabled={sendMessage.isPending}
      />
      <button
        type="submit"
        className={`bg-ducky-text text-white px-4 py-2 transition-opacity
          ${sendMessage.isPending ? "opacity-50" : "hover:opacity-90"}`}
        disabled={sendMessage.isPending}
      >
        {sendMessage.isPending ? "Sending..." : "Send"}
      </button>
    </form>
  );
}
