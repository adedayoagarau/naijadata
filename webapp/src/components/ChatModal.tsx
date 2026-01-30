"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { X, Send, Download, Loader2 } from "lucide-react";

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
  initialQuestion?: string;
}

export function ChatModal({ isOpen, onClose, initialQuestion }: ChatModalProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to Decide9ja. I can answer questions about Nigerian government budgets. Try asking about any ministry, agency, or budget line.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasProcessedInitial, setHasProcessedInitial] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(async (userMessage: string) => {
    if (!userMessage.trim() || isLoading) return;

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
  }, [isLoading, messages]);

  // Handle initial question when modal opens
  useEffect(() => {
    if (isOpen && initialQuestion && !hasProcessedInitial) {
      setHasProcessedInitial(true);
      sendMessage(initialQuestion);
    }
    if (!isOpen) {
      setHasProcessedInitial(false);
    }
  }, [isOpen, initialQuestion, hasProcessedInitial, sendMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    await sendMessage(userMessage);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="relative w-full md:max-w-lg h-[85vh] md:h-[600px] bg-[#050505] border border-gray-700 flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-label="Budget chat"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-[#25D366] rounded-full animate-pulse" />
            <span className="text-sm font-semibold">Budget Chat</span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 border border-gray-700 flex items-center justify-center hover:bg-white hover:text-black transition-colors"
            aria-label="Close chat"
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
                <div className="text-[10px] font-medium mb-1 opacity-60">
                  {message.role === "user" ? "You" : "Decide9ja"}
                </div>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>

                {message.data?.amount && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <div className="font-mono text-2xl text-[#25D366] font-bold">
                      {message.data.amount}
                    </div>
                    {message.data.comparison && (
                      <div className="text-xs mt-1 bg-white text-black px-2 py-0.5 inline-block font-semibold">
                        {message.data.comparison}
                      </div>
                    )}
                    <button className="mt-2 flex items-center gap-2 text-xs border border-[#25D366] text-[#25D366] px-2 py-1 hover:bg-[#25D366] hover:text-black transition-colors">
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
                <div className="text-[10px] font-medium mb-1 opacity-60">
                  Decide9ja
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing budget data...
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="p-3 border-t border-gray-800 bg-[#0a0a0a]"
        >
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about budgets..."
              className="flex-1 bg-[#111] border border-gray-800 p-3 text-sm text-white focus:outline-none focus:border-[#25D366]"
              disabled={isLoading}
              aria-label="Type your question"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="w-12 h-12 bg-[#25D366] text-black flex items-center justify-center hover:bg-[#20bd5a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
