import React from "react";
export function Badge({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border border-white/20 text-white bg-white/10 ${className}`}>
      {children}
    </span>
  );
}
