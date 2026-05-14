import React from "react";
import Link from "next/link";
import { MessageSquare, LayoutDashboard, Settings, PlusCircle } from "lucide-react";

export function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col bg-slate-950 text-slate-300">
      <div className="p-4">
        <h2 className="mb-6 px-2 text-lg font-bold tracking-tight text-white">
          SHL AI Assistant
        </h2>
        <Link href="/chat">
          <button className="flex w-full items-center gap-2 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700">
            <PlusCircle size={16} />
            New Chat
          </button>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        <nav className="space-y-1 px-2">
          <Link
            href="/chat"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white"
          >
            <MessageSquare size={18} />
            Chat
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white"
          >
            <LayoutDashboard size={18} />
            Dashboard
          </Link>
          <Link
            href="/settings"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white"
          >
            <Settings size={18} />
            Settings
          </Link>
        </nav>
      </div>

      <div className="p-4 text-xs text-slate-500">
        <p>SHL Recruiter App v1.0</p>
      </div>
    </div>
  );
}
