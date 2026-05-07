import { createFileRoute } from "@tanstack/react-router";
import { Stub } from "./my-simulations";
export const Route = createFileRoute("/settings")({
  component: () => Stub("Settings", "Customize your experience."),
});
