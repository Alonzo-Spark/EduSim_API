import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { getSubject, getClass } from "@/data/curriculum";
import { Card, PageWrapper } from "@/components/Card";
import { Crumbs } from "@/components/Crumbs";

export const Route = createFileRoute("/chapters/$classId/$subject")({
  component: ChaptersPage,
  loader: ({ params }) => {
    const c = getClass(Number(params.classId));
    const s = getSubject(Number(params.classId), params.subject);
    if (!c || !s) throw notFound();
    return { c, s };
  },
});

function ChaptersPage() {
  const { c, s } = Route.useLoaderData();
  const chapters = Array.isArray(s.chapters) ? s.chapters : [];
  const chapterCount = chapters.length;

  return (
    <PageWrapper>
      <Crumbs
        items={[
          { label: "Home", to: "/" },
          { label: c.name, to: "/subjects/$classId", params: { classId: String(c.id) } },
          { label: s.name },
        ]}
      />

      <h1 className="text-3xl font-bold mb-2">
        {s.name} <span className="text-muted-foreground text-lg">— Chapters</span>
      </h1>

      <p className="text-muted-foreground mb-8">{chapterCount} chapters available</p>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {chapters.map((chapter, i) => (
          <Link
            key={chapter.name}
            to="/topics/$classId/$subject/$chapter"
            params={{
              classId: String(c.id),
              subject: s.id,
              chapter: chapter.name,
            }}
          >
            <Card delay={i * 0.02}>
              <div className="text-xs text-cyan-400 mb-2">CHAPTER</div>

              <div className="text-lg font-bold mb-2">{chapter.name}</div>

              <p className="text-xs text-muted-foreground">
                Chapter {i + 1} of {chapters.length}
              </p>
            </Card>
          </Link>
        ))}
      </div>
    </PageWrapper>
  );
}
