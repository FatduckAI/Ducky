"use client";

import { Message } from "@/app/api/message/route";

const sendMessage = async (message: Partial<Message>) => {
  const response = await fetch("/api/message", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(message),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || "Failed to send message");
  }

  return response.json();
};

export default function MessageForm() {
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await sendMessage({
        user_id: "123",
        platform: "Discord",
        content: "Hello from Next.js!",
        priority: "Normal",
      });
      // Handle success
    } catch (error) {
      // Handle error
      console.error("Failed to send message:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="user_id" />
      <input type="text" name="platform" />
      <input type="text" name="content" />
      <input type="text" name="priority" />
    </form>
  );
}
