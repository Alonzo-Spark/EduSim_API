import { createFileRoute, useNavigate, notFound, redirect } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { getClass } from "@/data/curriculum";
import { PageWrapper } from "@/components/Card";
import { Crumbs } from "@/components/Crumbs";
import { Play } from "lucide-react";

export const Route = createFileRoute("/topics/$classId/$subject/$chapter")({
  beforeLoad: ({ params }) => {
    if (
      params.classId === "9" &&
      params.subject === "physics" &&
      params.chapter.toUpperCase() === "LAWS OF MOTION"
    ) {
      throw redirect({
        to: "/simulation/class9/physics/laws-of-motion",
      });
    }
  },
  component: TopicsPage,
  loader: ({ params }) => {
    const c = getClass(Number(params.classId));
    if (!c) throw notFound();

    const s = c.subjects.find((sub) => sub.id === params.subject);
    if (!s) throw notFound();

    if (!Array.isArray(s.chapters)) throw notFound();

    const chapter = s.chapters.find((ch) => ch.name === params.chapter);
    if (!chapter) throw notFound();

    return { c, s, chapter };
  },
});

function TopicsPage() {
  const { c, s, chapter } = Route.useLoaderData();
  const navigate = useNavigate();

  return (
    <PageWrapper>
      <Crumbs
        items={[
          { label: "Home", to: "/" },
          { label: c.name, to: "/subjects/$classId", params: { classId: String(c.id) } },
          {
            label: s.name,
            to: "/chapters/$classId/$subject",
            params: { classId: String(c.id), subject: s.id },
          },
          { label: chapter.name },
        ]}
      />

      <h1 className="text-3xl font-bold mb-2">
        {chapter.name} <span className="text-muted-foreground text-lg font-normal">— Topics</span>
      </h1>

      <p className="text-muted-foreground mb-8">{chapter.topics.length} topics available</p>

      <div className="space-y-3">
        {chapter.topics.map((topic, i) => (
          <motion.div
            key={topic.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className="glass rounded-2xl p-5 flex items-center justify-between gap-4 hover:neon-border transition-shadow"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--neon-purple)]/40 to-[var(--neon-cyan)]/30 flex items-center justify-center font-mono text-sm">
                {String(i + 1).padStart(2, "0")}
              </div>

              <div>
                <h3 className="font-semibold">{topic.name}</h3>

                <p className="text-xs text-muted-foreground">
                  {topic.hasSimulation ? "Interactive simulation available" : "Theory topic"}
                </p>
              </div>
            </div>

            {topic.hasSimulation && topic.simulationRoute ? (
              <motion.button
                whileHover={{ scale: 1.06 }}
                whileTap={{ scale: 0.96 }}
                onClick={() =>
                  navigate({
                    to: topic.simulationRoute,
                  })
                }
                className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white text-sm font-medium hover:glow-purple transition-shadow"
              >
                <Play className="w-4 h-4" /> Simulate
              </motion.button>
            ) : (
              <div className="text-xs text-muted-foreground">No simulation</div>
            )}
          </motion.div>
        ))}
      </div>
    </PageWrapper>
  );
}
