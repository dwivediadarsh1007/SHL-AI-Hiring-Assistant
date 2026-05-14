import React from "react";
import { Menu } from "lucide-react";
import { Button } from "../ui/button";

interface NavbarProps {
  onMenuClick?: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onMenuClick}
        >
          <Menu size={20} />
          <span className="sr-only">Toggle menu</span>
        </Button>
        <div className="font-semibold md:hidden">SHL AI Assistant</div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-medium text-white">
          HR
        </div>
      </div>
    </header>
  );
}
