import { UploadForm } from "@/components/upload-form";
import { HeroCard } from "@/components/hero-card";

export default function HomePage() {
  return (
    <main className="grid gap-6 md:grid-cols-2">
      <HeroCard />
      <section>
        <UploadForm />
      </section>
    </main>
  );
}
