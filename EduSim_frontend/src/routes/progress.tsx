import { createFileRoute } from "@tanstack/react-router";
import { Stub } from "./my-simulations";
export const Route = createFileRoute("/progress")({
  component: () => Stub("Progress", "Track your learning journey."),
});
