import { createFileRoute } from "@tanstack/react-router";
import { PageWrapper } from "@/components/Card";
import { SimulationStudio } from "@/components/simulation-runtime/SimulationStudio";

export const Route = createFileRoute("/ai-agent")({
  component: AIAgentPage,
});

function AIAgentPage() {
  return (
    <PageWrapper>
      <SimulationStudio />
    </PageWrapper>
  );
}
