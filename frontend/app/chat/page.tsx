"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { chatAPI } from "@/lib/api";
import { Message, AssessmentRecommendation } from "@/types/api";

interface ChatTurn {
  id: string;
  userMessage: Message;
  assistantMessage?: Message;
  recommendations?: AssessmentRecommendation[];
  isLoading: boolean;
}

export default function ChatPage() {
  const [inputValue, setInputValue] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [turns]);

  const handleSubmit = async () => {
    if (!inputValue.trim()) return;

    const userMsg: Message = { role: "user", content: inputValue };
    const newTurnId = Date.now().toString();
    
    setTurns((prev) => [
      ...prev,
      { id: newTurnId, userMessage: userMsg, isLoading: true },
    ]);
    setInputValue("");
    setIsTyping(true);

    try {
      // Build conversation history for API
      const history: Message[] = [];
      turns.forEach(turn => {
        history.push(turn.userMessage);
        if (turn.assistantMessage) history.push(turn.assistantMessage);
      });
      history.push(userMsg);

      const response = await chatAPI.sendMessage(history);
      
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === newTurnId
            ? {
                ...turn,
                isLoading: false,
                assistantMessage: { role: "assistant", content: response.reply },
                recommendations: response.recommendations,
              }
            : turn
        )
      );
    } catch (error) {
      console.error("Chat error:", error);
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === newTurnId
            ? {
                ...turn,
                isLoading: false,
                assistantMessage: {
                  role: "assistant",
                  content: "Sorry, I encountered an error. Please make sure the backend server is running and your API key is valid.",
                },
              }
            : turn
        )
      );
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex-1 overflow-y-auto pb-32">
        {turns.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center p-8 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-blue-600">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1 className="mb-2 text-2xl font-bold text-slate-900">How can I help you hire today?</h1>
            <p className="max-w-md text-slate-500">
              Describe the role you are hiring for, and I'll recommend the best SHL assessments from our catalog.
            </p>
          </div>
        ) : (
          <div className="flex flex-col">
            {turns.map((turn) => (
              <React.Fragment key={turn.id}>
                <ChatMessage message={turn.userMessage} />
                {turn.isLoading ? (
                  <div className="flex w-full bg-slate-50 py-6">
                    <div className="mx-auto flex w-full max-w-3xl gap-4 px-4 md:px-0">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white">
                        <svg className="h-4 w-4 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                      </div>
                      <div className="flex items-center text-sm font-medium text-slate-500">
                        Analyzing request...
                      </div>
                    </div>
                  </div>
                ) : turn.assistantMessage ? (
                  <ChatMessage 
                    message={turn.assistantMessage} 
                    recommendations={turn.recommendations} 
                  />
                ) : null}
              </React.Fragment>
            ))}
            <div ref={scrollRef} />
          </div>
        )}
      </div>
      
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent md:pl-64">
        <div className="px-4 pb-4">
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSubmit}
            isLoading={isTyping}
          />
          <div className="text-center text-xs text-slate-400 pb-2">
            AI Assistant can make mistakes. Verify assessments before sending to candidates.
          </div>
        </div>
      </div>
    </div>
  );
}
