/**
 * Loading Spinner Component
 */

import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  className?: string;
}

export function LoadingSpinner({ className }: LoadingSpinnerProps) {
  return (
    <div className={cn("inline-block", className)}>
      <div className="animate-spin rounded-full border-2 border-transparent border-t-current border-r-current" />
    </div>
  );
}
