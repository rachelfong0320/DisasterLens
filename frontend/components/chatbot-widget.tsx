"use client";

import { useState, useRef, useEffect } from "react";
import { AlertTriangle, Zap, Send, X, Bot } from "lucide-react";
import { useTranslations } from "next-intl";

interface ChatMessage {
  id: string;
  type: "user" | "bot";
  message: string;
  timestamp: Date;
}

interface ChatbotWidgetProps {
  isOpen: boolean;
  onToggle: (open: boolean) => void;
}

export default function ChatbotWidget({
  isOpen,
  onToggle,
}: ChatbotWidgetProps) {
  const t = useTranslations("ChatbotWidget");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      type: "bot",
      message: t("chat"),
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userTextInput = input; // Capture input before clearing state
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      message: userTextInput,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput(""); // Clear input immediately for better UX
    setIsTyping(true);

    try {
      // 1. Call your FastAPI backend
      const response = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userTextInput }),
      });

      if (!response.ok) {
        throw new Error("Failed to connect to disaster service");
      }

      const data = await response.json();

      // 2. Map the backend "reply" to a bot message
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        message: data.reply,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      // Handle connection errors gracefully
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        message:
          "Sorry, I'm having trouble connecting to the disaster database. Please try again later.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => onToggle(!isOpen)}
        className="fixed bottom-6 right-6 bg-primary text-primary-foreground rounded-full p-4 shadow-lg hover:opacity-90 transition z-40 text-2xl"
        aria-label="Toggle chatbot"
      >
        <div className="absolute inset-0 rounded-full bg-primary animate-ping opacity-20" />
        <div className="relative z-10 flex items-center justify-center">
          {isOpen ? (
            <X className="w-6 h-6" />
          ) : (
            <>
              <Bot className="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-destructive rounded-full animate-pulse" />
            </>
          )}
        </div>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 bg-card border-2 border-primary/20 rounded-2xl shadow-2xl flex flex-col z-1000 h-[32rem] max-h-[85vh] animate-in slide-in-from-bottom-5 duration-300">
          <div className="relative bg-gradient-to-r from-primary via-primary to-primary/90 text-primary-foreground px-6 py-4 rounded-t-2xl overflow-hidden">
            {/* Animated background pattern */}
            <div className="absolute inset-0 opacity-50">
              <div className="absolute top-2 left-4">
                <AlertTriangle className="w-8 h-8 animate-pulse" />
              </div>
              <div className="absolute bottom-2 right-4">
                <Zap className="w-6 h-6 animate-bounce" />
              </div>
            </div>

            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <h3 className="font-bold text-lg tracking-tight">
                  DisasterLens AI Chatbot
                </h3>
              </div>
              <p className="text-xs opacity-90 font-medium">{t("desc")}</p>
            </div>

            {/* Decorative corner accent */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-primary-foreground/5 rounded-bl-full" />
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gradient-to-b from-background/50 to-background">
            {messages.map((msg, idx) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.type === "user" ? "justify-end" : "justify-start"
                } animate-in slide-in-from-bottom-2 duration-300`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className="flex items-start gap-2 max-w-[85%]">
                  {msg.type === "bot" && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm shadow-sm backdrop-blur-sm ${
                      msg.type === "user"
                        ? "bg-primary text-primary-foreground rounded-tr-sm shadow-primary/20"
                        : "bg-secondary/80 text-foreground border border-border/50 rounded-tl-sm"
                    }`}
                  >
                    <p className="leading-relaxed">{msg.message}</p>
                    <span className="text-[10px] opacity-60 mt-1 block">
                      {msg.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  {msg.type === "user" && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center mt-1">
                      <div className="w-4 h-4 rounded-full bg-primary" />
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start animate-in fade-in duration-200">
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-secondary/80 border border-border/50">
                    <div className="flex gap-1">
                      <div
                        className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
                        style={{ animationDelay: "0ms" }}
                      />
                      <div
                        className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      />
                      <div
                        className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t-2 border-primary/10 p-4 bg-card/95 backdrop-blur-sm rounded-b-2xl">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-3 h-3 text-primary animate-pulse" />
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">
                {t("chatdesc")}
              </span>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                placeholder={t("placeholder")}
                className="flex-1 px-4 py-3 border-2 border-primary/20 rounded-xl bg-background/50 text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all placeholder:text-muted-foreground/60"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="bg-primary text-primary-foreground p-3 rounded-xl hover:bg-primary/90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20 group"
                aria-label="Send message"
              >
                <Send className="w-5 h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
