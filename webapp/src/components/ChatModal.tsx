"use client";

import { useState, useRef, useEffect } from "react";
import { X, Send, Download } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: {
    amount?: string;
    comparison?: string;
  };
}

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatModal({ isOpen, onClose }: ChatModalProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to Decide9ja. I can answer questions about Nigerian government budgets. Try asking: 'How much did NIA spend on hospitals?' or 'Compare NASS travel to Health drugs budget'",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          history: messages,
        }),
      });

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          data: data.data,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full md:max-w-lg h-[85vh] md:h-[600px] bg-black border-2 border-white flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-white">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-[#25D366] rounded-full animate-pulse" />
            <span className="font-mono text-sm uppercase">Budget_Chat</span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 border border-white flex items-center justify-center hover:bg-white hover:text-black transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[85%] ${
                  message.role === "user"
                    ? "bg-[#25D366] text-black"
                    : "bg-[#111] border border-gray-800"
                } p-3`}
              >
                <div className="text-[10px] font-mono uppercase mb-1 opacity-60">
                  {message.role === "user" ? "YOU" : "DECIDE9JA"}
                </div>
                <p className="font-mono text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>

                {message.data?.amount && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <div className="font-pixel text-2xl text-[#25D366]">
                      {message.data.amount}
                    </div>
                    {message.data.comparison && (
                      <div className="text-xs mt-1 bg-white text-black px-1 inline-block">
                        {message.data.comparison}
                      </div>
                    )}
                    <button className="mt-2 flex items-center gap-2 text-[10px] font-mono uppercase border border-[#25D366] text-[#25D366] px-2 py-1 hover:bg-[#25D366] hover:text-black transition-colors">
                      <Download size={12} /> Generate Card
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-[#111] border border-gray-800 p-3">
                <div className="text-[10px] font-mono uppercase mb-1 opacity-60">
                  DECIDE9JA
                </div>
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-[#25D366] animate-pulse" />
                  <div className="w-2 h-2 bg-[#25D366] animate-pulse delay-100" />
                  <div className="w-2 h-2 bg-[#25D366] animate-pulse delay-200" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="p-3 border-t border-white bg-black"
        >
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center border border-white bg-[#0a0a0a]">
              <span className="pl-3 text-[#25D366] font-bold">&gt;</span>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about budgets..."
                className="w-full bg-transparent p-2 font-mono text-sm text-white focus:outline-none"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="w-10 h-10 bg-[#25D366] text-black flex items-center justify-center hover:bg-white transition-colors disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
