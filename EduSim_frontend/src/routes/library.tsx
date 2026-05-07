import { createFileRoute } from "@tanstack/react-router";
import { Stub } from "./my-simulations";
export const Route = createFileRoute("/library")({
  component: () => Stub("Library", "Browse the full simulation library."),
});
