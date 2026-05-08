import { Link, useRouterState } from "@tanstack/react-router";
import {
  Home,
  Library,
  Heart,
  BarChart3,
  User,
  Settings,
  Sparkles,
  Rocket,
  Zap,
  Atom,
  GraduationCap,
} from "lucide-react";

const items = [
  { to: "/", label: "Home", icon: Home },
  { to: "/ai-agent", label: "AI Agent", icon: Sparkles, badge: "NEW" },
  { to: "/tutor", label: "Tutor", icon: GraduationCap },
  { to: "/my-simulations", label: "My Simulations", icon: Rocket },
  { to: "/library", label: "Library", icon: Library },
  { to: "/favorites", label: "Favorites", icon: Heart },
  { to: "/progress", label: "Progress", icon: BarChart3 },
  { to: "/profile", label: "Profile", icon: User },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const path = useRouterState({ select: (s) => s.location.pathname });
  return (
    <aside className="hidden md:flex flex-col w-64 shrink-0 glass-strong rounded-3xl m-4 p-6 sticky top-4 h-[calc(100vh-2rem)]">
      <Link to="/" className="flex items-center gap-2 mb-10">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-blue)] flex items-center justify-center glow-purple">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold text-gradient">EduSim</span>
      </Link>
      <nav className="flex flex-col gap-1 flex-1">
        {items.map((it) => {
          const active = it.to === "/" ? path === "/" : path.startsWith(it.to);
          const Icon = it.icon;
          return (
            <Link
              key={it.to}
              to={it.to}
              className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${
                active
                  ? "bg-gradient-to-r from-[var(--neon-purple)]/30 to-[var(--neon-blue)]/20 text-foreground neon-border"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{it.label}</span>
              {it.badge && (
                <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-lg bg-gradient-to-r from-[var(--neon-purple)]/40 to-[var(--neon-cyan)]/40 text-[var(--neon-cyan)]">
                  {it.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
