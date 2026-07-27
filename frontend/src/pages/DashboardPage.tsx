import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getDashboardStats } from "../api/documents";
import { listConversations } from "../api/chat";
import DocumentCard from "../components/DocumentCard";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-black/5 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-ink/40">{label}</p>
      <p className="mt-2 font-display text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboardStats });
  const { data: conversations } = useQuery({ queryKey: ["conversations"], queryFn: listConversations });

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-ink">Dashboard</h1>
        <Link
          to="/upload"
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent/90"
        >
          Upload document
        </Link>
      </div>

      {isLoading ? (
        <p className="mt-8 text-sm text-ink/50">Loading...</p>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <StatCard label="Documents" value={stats?.total_documents ?? 0} />
            <StatCard label="Chats" value={stats?.total_chats ?? 0} />
            <StatCard label="Storage used" value={formatBytes(stats?.storage_used_bytes ?? 0)} />
          </div>

          <div className="mt-10">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-base font-semibold text-ink">Recent documents</h2>
              <Link to="/upload" className="text-sm text-accent">View all</Link>
            </div>
            <div className="mt-4 space-y-3">
              {stats?.recent_documents.length ? (
                stats.recent_documents.map((doc) => <DocumentCard key={doc.id} doc={doc} />)
              ) : (
                <p className="text-sm text-ink/40">No documents yet — upload one to get started.</p>
              )}
            </div>
          </div>

          <div className="mt-10">
            <h2 className="font-display text-base font-semibold text-ink">Recent chats</h2>
            <div className="mt-4 space-y-2">
              {conversations && conversations.length > 0 ? (
                conversations.slice(0, 5).map((c) => (
                  <Link
                    key={c.id}
                    to={`/chat?conversationId=${c.id}`}
                    className="block rounded-xl border border-black/5 bg-white px-4 py-3 text-sm text-ink hover:shadow-sm transition"
                  >
                    {c.title}
                  </Link>
                ))
              ) : (
                <p className="text-sm text-ink/40">No conversations yet.</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
