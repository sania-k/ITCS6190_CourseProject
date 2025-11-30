"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Bot, User } from "lucide-react"

const botResponses = {
  jokes: [
    "Why don't planes ever get lost? Because they always follow their flight plan! ✈️",
    "What do you call a flying airplane without passengers? An AirPLAINE! 😄",
    "Why did the airplane get sent to his room? Bad altitude! 🛫",
    "What's a pilot's favorite type of bagel? Plain! 🥯",
    "Why do flight attendants make great friends? They're always up-lifting! ☁️",
  ],
  questions: [
    "What's your favorite travel destination? 🌍",
    "Window seat or aisle seat? 🪟",
    "What's the most interesting place you've ever flown to? ✈️",
    "Coffee or tea during flights? ☕",
    "Ever had a crazy airport story? Share it! 📖",
  ],
  greetings: [
    "Hey there, traveler! Ready to chat while we wait? 😊",
    "Welcome to the Chill Zone! How's your day going? ☀️",
    "Hi! Need a break from flight planning? Let's chat! 💬",
  ],
}

type Message = {
  text: string
  sender: "user" | "bot"
  timestamp: Date
}

export function ChillZone() {
  const [messages, setMessages] = useState<Message[]>([
    {
      text: "Hey there! 👋 I'm your SkyWatch companion bot. While you're checking delays, let's have some fun! Type 'joke' for a laugh or 'question' for a fun question!",
      sender: "bot",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const generateBotResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase()

    if (lowerMessage.includes("joke") || lowerMessage.includes("funny")) {
      return botResponses.jokes[Math.floor(Math.random() * botResponses.jokes.length)]
    }

    if (lowerMessage.includes("question") || lowerMessage.includes("ask me")) {
      return botResponses.questions[Math.floor(Math.random() * botResponses.questions.length)]
    }

    if (lowerMessage.includes("hello") || lowerMessage.includes("hi") || lowerMessage.includes("hey")) {
      return botResponses.greetings[Math.floor(Math.random() * botResponses.greetings.length)]
    }

    if (lowerMessage.includes("flight") || lowerMessage.includes("delay")) {
      return "I see you're thinking about flights! Don't worry, our predictor has got you covered. Need a distraction? Ask me for a joke! 😄"
    }

    if (lowerMessage.includes("weather")) {
      return "Ah, weather! The eternal frenemy of aviation. ☁️ Fun fact: Did you know that pilots actually welcome light rain? It cools the engines! 🌧️"
    }

    const randomResponses = [
      "That's interesting! Tell me more about your travels! ✈️",
      "I love chatting with travelers! What's on your mind? 💭",
      "Nice! Want to hear a joke? Just say 'joke'! 😊",
      "Cool beans! Ask me a question by typing 'question'! 🎯",
      "Awesome! I'm here to keep you entertained while you wait! 🎉",
    ]

    return randomResponses[Math.floor(Math.random() * randomResponses.length)]
  }

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: Message = {
      text: input,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")

    // Bot response after a short delay
    setTimeout(() => {
      const botMessage: Message = {
        text: generateBotResponse(input),
        sender: "bot",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botMessage])
    }, 800)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSend()
    }
  }

  return (
    <section id="chill-zone" className="bg-muted/30 py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-3xl">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-balance text-4xl font-bold">Chill Zone</h2>
            <p className="text-pretty text-muted-foreground leading-relaxed">
              {"Relax and chat with our friendly bot while you wait for your flight info!"}
            </p>
          </div>

          <Card className="border-2 shadow-lg">
            <CardHeader className="border-b bg-primary/5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
                  <Bot className="h-6 w-6 text-primary-foreground" />
                </div>
                <div>
                  <CardTitle>SkyWatch Companion</CardTitle>
                  <CardDescription>Your entertainment hub</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[400px] p-4" ref={scrollRef}>
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex gap-3 ${message.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
                    >
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                          message.sender === "bot" ? "bg-primary" : "bg-secondary"
                        }`}
                      >
                        {message.sender === "bot" ? (
                          <Bot className="h-4 w-4 text-primary-foreground" />
                        ) : (
                          <User className="h-4 w-4 text-secondary-foreground" />
                        )}
                      </div>
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          message.sender === "bot" ? "bg-muted text-foreground" : "bg-primary text-primary-foreground"
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{message.text}</p>
                        <p
                          className={`mt-1 text-xs ${
                            message.sender === "bot" ? "text-muted-foreground" : "text-primary-foreground/70"
                          }`}
                        >
                          {message.timestamp.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>

              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type 'joke' or 'question' to get started..."
                    className="flex-1"
                  />
                  <Button onClick={handleSend} size="icon" disabled={!input.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  {'Try: "joke", "question", "hello", or just chat naturally!'}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}
