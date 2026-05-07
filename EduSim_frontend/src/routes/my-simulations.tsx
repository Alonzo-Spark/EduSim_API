import { createFileRoute } from "@tanstack/react-router";
import { PageWrapper } from "@/components/Card";

export const Route = createFileRoute("/my-simulations")({
  component: () => Stub("My Simulations", "Your launched simulations will appear here."),
});
export function Stub(title: string, subtitle: string) {
  return (
    <PageWrapper>
      <div className="glass-strong rounded-3xl p-12 text-center">
        <h1 className="text-3xl font-bold text-gradient mb-2">{title}</h1>
        <p className="text-muted-foreground">{subtitle}</p>
      </div>
    </PageWrapper>
  );
}
