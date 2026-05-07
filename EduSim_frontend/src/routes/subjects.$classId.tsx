import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { getClass, type ClassInfo } from "@/data/curriculum";
import { Card, PageWrapper } from "@/components/Card";
import { Crumbs } from "@/components/Crumbs";
import * as Icons from "lucide-react";

export const Route = createFileRoute("/subjects/$classId")({
  component: SubjectsPage,
  loader: ({ params }) => {
    const c = getClass(Number(params.classId));
    if (!c) throw notFound();
    return c;
  },
  notFoundComponent: () => <div className="glass rounded-3xl p-8">Class not found.</div>,
  errorComponent: ({ error }) => <div className="glass rounded-3xl p-8">{error.message}</div>,
});

function SubjectsPage() {
  const c = Route.useLoaderData() as ClassInfo;
  return (
    <PageWrapper>
      <Crumbs items={[{ label: "Home", to: "/" }, { label: c.name }]} />
      <h1 className="text-3xl font-bold mb-2">
        {c.name} <span className="text-muted-foreground text-lg font-normal">— Subjects</span>
      </h1>
      <p className="text-muted-foreground mb-8">{c.description}</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {c.subjects.map((s, i) => {
          const Icon = (Icons as any)[s.icon] ?? Icons.BookOpen;
          const chapterCount = Array.isArray(s.chapters) ? s.chapters.length : s.chapters;
          return (
            <Link
              key={s.id}
              to="/chapters/$classId/$subject"
              params={{ classId: String(c.id), subject: s.id }}
            >
              <Card delay={i * 0.05}>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)]/40 to-[var(--neon-blue)]/30 flex items-center justify-center mb-4 group-hover:glow-purple transition-shadow">
                  <Icon className="w-7 h-7 text-[var(--neon-cyan)]" />
                </div>
                <h3 className="text-xl font-bold mb-1">{s.name}</h3>
                <p className="text-sm text-muted-foreground mb-4">{s.description}</p>
                <div className="text-xs font-mono text-[var(--neon-cyan)]">
                  {chapterCount} CHAPTERS
                </div>
              </Card>
            </Link>
          );
        })}
      </div>
    </PageWrapper>
  );
}
