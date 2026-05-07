import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { CLASSES } from "@/data/curriculum";
import { Card, PageWrapper } from "@/components/Card";
import { Rocket, Sparkles, BookOpen, Atom } from "lucide-react";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return (
    <PageWrapper>
      <section className="glass-strong rounded-3xl p-8 md:p-12 mb-10 relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-[var(--neon-purple)]/30 blur-3xl" />
        <div className="absolute -bottom-20 -left-10 w-72 h-72 rounded-full bg-[var(--neon-cyan)]/20 blur-3xl" />
        <div className="relative grid md:grid-cols-[1fr_auto] items-center gap-8">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-4xl md:text-5xl font-bold mb-3"
            >
              Welcome to <span className="text-gradient">EduSim</span> 👋
            </motion.h1>
            <p className="text-muted-foreground max-w-xl text-base md:text-lg">
              Select a class to explore subjects and start your learning journey through interactive
              simulations.
            </p>
            <div className="flex gap-3 mt-6">
              <div className="flex items-center gap-2 glass px-4 py-2 rounded-2xl text-sm">
                <Sparkles className="w-4 h-4 text-[var(--neon-cyan)]" /> 100+ Simulations
              </div>
              <div className="flex items-center gap-2 glass px-4 py-2 rounded-2xl text-sm">
                <BookOpen className="w-4 h-4 text-[var(--neon-purple)]" /> Class 1–10
              </div>
            </div>
          </div>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="hidden md:flex w-48 h-48 rounded-full bg-gradient-to-br from-[var(--neon-purple)] via-[var(--neon-blue)] to-[var(--neon-cyan)] items-center justify-center glow-purple"
          >
            <Rocket className="w-24 h-24 text-white" />
          </motion.div>
        </div>
      </section>

      <h2 className="text-2xl font-bold mb-6">Choose your class</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {CLASSES.map((c, i) => (
          <Link key={c.id} to="/subjects/$classId" params={{ classId: String(c.id) }}>
            <Card delay={i * 0.04}>
              <div className="text-xs text-[var(--neon-cyan)] font-mono mb-2">CLASS</div>
              <div className="text-3xl font-bold text-gradient mb-2">{c.id}</div>
              <p className="text-xs text-muted-foreground line-clamp-2">{c.description}</p>
              <div className="mt-3 text-xs text-muted-foreground">{c.subjects.length} subjects</div>
            </Card>
          </Link>
        ))}
      </div>
    </PageWrapper>
  );
}
