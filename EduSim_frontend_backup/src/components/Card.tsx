import React from "react";

export function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="space-y-6 pb-10">
      {children}
    </div>
  );
}
