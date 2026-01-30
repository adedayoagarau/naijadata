"use client";

import { useState } from "react";
import { Search } from "lucide-react";

interface ChatInputProps {
  onSubmit: (question: string) => void;
  placeholder?: string;
}

export function ChatInput({ onSubmit, placeholder = "Ask anything about the budget..." }: ChatInputProps) {
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
      <label htmlFor="budget-search" className="sr-only">
        Search the budget
      </label>
      <div className="flex items-center border border-gray-700 bg-[#0a0a0a] hover:border-gray-500 focus-within:border-[#25D366] transition-colors">
        <Search className="w-5 h-5 text-gray-600 ml-3" />
        <input
          id="budget-search"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-transparent p-3 text-sm text-white focus:outline-none placeholder-gray-600"
        />
        <button
          type="submit"
          className="px-4 py-2 mr-2 bg-[#25D366] text-black text-xs font-semibold
            hover:bg-[#20bd5a] transition-colors disabled:opacity-50"
          disabled={!input.trim()}
        >
          Ask
        </button>
      </div>
    </form>
  );
}
