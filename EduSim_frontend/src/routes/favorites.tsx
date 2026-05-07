import { createFileRoute } from "@tanstack/react-router";
import { Stub } from "./my-simulations";
export const Route = createFileRoute("/favorites")({
  component: () => Stub("Favorites", "Your saved simulations."),
});
