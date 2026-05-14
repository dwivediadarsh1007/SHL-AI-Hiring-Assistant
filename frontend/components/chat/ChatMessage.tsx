import React from "react";
import { User, Bot } from "lucide-react";
import { Message, AssessmentRecommendation } from "../../types/api";
import { cn } from "@/lib/utils";
import { RecommendationCard } from "./RecommendationCard";

interface ChatMessageProps {
  message: Message;
  recommendations?: AssessmentRecommendation[];
}

export function ChatMessage({ message, recommendations }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex w-full py-6", isUser ? "bg-white" : "bg-slate-50")}>
      <div className="mx-auto flex w-full max-w-3xl gap-4 px-4 md:px-0">
        <div className="flex shrink-0 pt-1">
          {isUser ? (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white">
              <User size={18} />
            </div>
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-white">
              <Bot size={18} />
            </div>
          )}
        </div>
        <div className="flex flex-col gap-3 min-w-0 flex-1">
          <div className="font-semibold text-sm text-slate-900">
            {isUser ? "You" : "SHL Assistant"}
          </div>
          <div className="prose prose-sm prose-slate max-w-none text-slate-700 whitespace-pre-wrap">
            {message.content}
          </div>
          
          {/* Render Recommendations if present */}
          {recommendations && recommendations.length > 0 && (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {recommendations.map((rec, idx) => (
                <RecommendationCard key={idx} assessment={rec} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
