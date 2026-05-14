import React from "react";
import { Send } from "lucide-react";
import { Button } from "../ui/button";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export function ChatInput({ value, onChange, onSubmit, isLoading }: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSubmit();
      }
    }
  };

  return (
    <div className="relative mx-auto flex w-full max-w-3xl items-center pb-6 pt-4">
      <div className="relative flex w-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm focus-within:ring-1 focus-within:ring-blue-600">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me to recommend an SHL assessment..."
          className="max-h-32 min-h-[56px] w-full resize-none bg-transparent px-4 py-4 pr-12 text-sm focus:outline-none"
          rows={1}
          disabled={isLoading}
        />
        <Button
          onClick={onSubmit}
          disabled={!value.trim() || isLoading}
          size="icon"
          className="absolute bottom-2 right-2 h-10 w-10 rounded-xl"
        >
          <Send size={18} />
        </Button>
      </div>
    </div>
  );
}
