import { UploadForm } from "@/components/upload-form";
import { JobList } from "@/components/job-list";

export default function InboxPage() {
  return (
    <main className="grid gap-6 md:grid-cols-2">
      <UploadForm />
      <section className="rounded-2xl border border-white/10 bg-slate-900/50 p-5">
        <JobList />
      </section>
    </main>
  );
}
