import { createFileRoute } from "@tanstack/react-router";
import { GeneMirrorApp } from "@/components/GeneMirrorApp";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "GeneMirror AI · Research Console" },
      { name: "description", content: "Explainable intelligence for genetic variant analysis." },
      { property: "og:title", content: "GeneMirror AI · Research Console" },
      { property: "og:description", content: "Explore genetic variants, sequence context, protein changes, and explainable model predictions." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return <GeneMirrorApp />;
}
