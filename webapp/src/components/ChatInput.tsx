"use client";

import { useState } from "react";

interface ChatInputProps {
  onSubmit: (question: string) => void;
}

export function ChatInput({ onSubmit }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
      setInput("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <label className="block text-[10px] uppercase mb-1 text-gray-500">
        Ask Decide9ja
      </label>
      <div className="flex items-center border-2 border-white bg-black">
        <span className="pl-3 text-[#25D366] font-bold text-lg">&gt;</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Why is NIA building hospitals?"
          className="w-full bg-transparent p-3 font-mono text-sm text-white focus:outline-none uppercase placeholder-gray-700"
        />
        <div className="w-3 h-5 bg-[#25D366] mr-3 cursor-blink" />
      </div>
    </form>
  );
}
