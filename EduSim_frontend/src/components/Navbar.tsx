import { Bell, Search } from "lucide-react";

export function Navbar() {
  return (
    <div className="flex items-center gap-4 mb-8">
      <div className="flex-1 glass rounded-2xl flex items-center px-4 py-3 gap-3">
        <Search className="w-4 h-4 text-muted-foreground" />
        <input
          placeholder="Search for topics, simulations…"
          className="bg-transparent outline-none flex-1 text-sm placeholder:text-muted-foreground"
        />
      </div>
      <button className="glass w-12 h-12 rounded-2xl flex items-center justify-center hover:text-[var(--neon-cyan)] transition-colors relative">
        <Bell className="w-5 h-5" />
        <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[var(--neon-purple)] glow-purple" />
      </button>
      <div className="glass rounded-2xl flex items-center gap-3 px-3 py-2">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-cyan)] flex items-center justify-center font-bold text-sm">
          S
        </div>
        <div className="hidden sm:block">
          <p className="text-xs text-muted-foreground">Hello,</p>
          <p className="text-sm font-semibold leading-none">Student!</p>
        </div>
      </div>
    </div>
  );
}
