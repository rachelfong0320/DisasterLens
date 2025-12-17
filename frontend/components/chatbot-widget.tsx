"use client"

import { useState, useRef, useEffect } from "react"

interface ChatMessage {
  id: string
  type: "user" | "bot"
  message: string
  timestamp: Date
}

interface ChatbotWidgetProps {
  isOpen: boolean
  onToggle: (open: boolean) => void
}

export default function ChatbotWidget({ isOpen, onToggle }: ChatbotWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      type: "bot",
      message: "Hello! How can I help you find disaster information today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      message: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])

    // Simulate bot response
    setTimeout(() => {
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        message: `I found recent ${input.toLowerCase()} events in Malaysia. Would you like to see more details?`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botMessage])
    }, 600)

    setInput("")
  }

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => onToggle(!isOpen)}
        className="fixed bottom-6 right-6 bg-primary text-primary-foreground rounded-full p-4 shadow-lg hover:opacity-90 transition z-40 text-2xl"
      >
        {isOpen ? "✕" : "💬"}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 bg-card border border-border rounded-lg shadow-2xl flex flex-col z-9999 h-96 max-h-[80vh]">
          {/* Header */}
          <div className="bg-primary text-primary-foreground px-4 py-3 rounded-t-lg">
            <h3 className="font-semibold">DisasterLens Chatbot</h3>
            <p className="text-xs opacity-90">Ask about disaster events</p>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                    msg.type === "user" ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground"
                  }`}
                >
                  {msg.message}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-border p-4 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about disasters..."
              className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
            />
            <button
              onClick={handleSend}
              className="bg-primary text-primary-foreground p-2 rounded-md hover:opacity-90 transition text-lg"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}
