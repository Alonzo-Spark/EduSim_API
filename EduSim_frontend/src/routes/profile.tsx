import { createFileRoute } from "@tanstack/react-router";
import { Stub } from "./my-simulations";
export const Route = createFileRoute("/profile")({
  component: () => Stub("Profile", "Manage your student profile."),
});
