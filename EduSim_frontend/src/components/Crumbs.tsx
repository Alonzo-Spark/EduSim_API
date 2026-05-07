import { Link } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";

export function Crumbs({ items }: { items: { label: string; to?: string; params?: any }[] }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6 flex-wrap">
      {items.map((it, i) => (
        <div key={i} className="flex items-center gap-2">
          {it.to ? (
            <Link
              to={it.to}
              params={it.params}
              className="hover:text-[var(--neon-cyan)] transition-colors"
            >
              {it.label}
            </Link>
          ) : (
            <span className="text-foreground font-medium">{it.label}</span>
          )}
          {i < items.length - 1 && <ChevronRight className="w-3 h-3" />}
        </div>
      ))}
    </div>
  );
}
