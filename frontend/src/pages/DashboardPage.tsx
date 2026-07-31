import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getDashboardStats, listDocuments, uploadDocument, deleteDocument } from "../api/documents";
import { listConversations, pinConversation, deleteConversation } from "../api/chat";
import { useAuth } from "../hooks/useAuth";
import DocumentCard from "../components/DocumentCard";
import FileUploader from "../components/FileUploader";

/* ─── Helpers ─── */
function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function greeting(name?: string | null) {
  const h = new Date().getHours();
  const salutation = h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  return name ? `${salutation}, ${name.split(" ")[0]}` : salutation;
}

/* ─── Skeleton ─── */
function StatSkeleton() {
  return <div className="skeleton h-24 rounded-3xl" />;
}

/* ─── Stat card ─── */
interface StatCardProps { label: string; value: string | number; icon: React.ReactNode; accent?: boolean; }
function StatCard({ label, value, icon, accent }: StatCardProps) {
  return (
    <div
      className={`group relative overflow-hidden rounded-3xl p-5 transition hover:-translate-y-0.5 hover:shadow-float ${
        accent
          ? "bg-card-gradient text-white shadow-glow-lg"
          : "bg-white border border-black/5 shadow-card text-ink"
      }`}
    >
      {accent && <div className="absolute -right-4 -top-4 h-20 w-20 rounded-full bg-white/10 blur-xl" />}
      <div className="relative z-10 flex items-start justify-between">
        <div>
          <p className={`text-xs font-semibold uppercase tracking-wide ${accent ? "text-white/70" : "text-t3"}`}>{label}</p>
          <p className={`mt-2 font-display text-3xl font-bold ${accent ? "text-white" : "text-ink"}`}>{value}</p>
        </div>
        <span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${accent ? "bg-white/20" : "bg-accentSoft"}`}>
          {icon}
        </span>
      </div>
    </div>
  );
}

/* ─── Empty state ─── */
function EmptyDocs() {
  return (
    <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-t4/60 bg-white py-14 text-center animate-fade-in">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accentSoft">
        <svg className="h-7 w-7 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p className="text-sm font-semibold text-ink">No documents yet</p>
      <p className="mt-1 text-xs text-t3">Upload your first file above to get started</p>
    </div>
  );
}

function EmptyChats() {
  return (
    <p className="py-6 text-center text-sm text-t3">
      No conversations yet — start a chat after uploading a document.
    </p>
  );
}

/* ─── Page ─── */
export default function DashboardPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const { data: stats, isLoading: isStatsLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboardStats });
  const { data: conversations } = useQuery({ queryKey: ["conversations"], queryFn: listConversations });

  const { data: documents, isLoading: isDocsLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      const docs = query.state.data as any[] | undefined;
      const stillWorking = docs?.some((d) => d.status === "pending" || d.status === "processing");
      return stillWorking ? 2000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setError("");
    },
    onError: (err: any) => setError(err?.response?.data?.detail || "Upload failed. Please try again."),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const pinChatMutation = useMutation({
    mutationFn: pinConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const handleUpload = (file: File) => {
    setError("");
    uploadMutation.mutate(file);
  };

  const readyCount     = documents?.filter((d) => d.status === "ready").length ?? 0;
  const processingCount = documents?.filter((d) => d.status === "processing" || d.status === "pending").length ?? 0;

  const icons = {
    docs: (
      <svg className="h-5 w-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    chat: (
      <svg className="h-5 w-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
    storage: (
      <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
      </svg>
    ),
  };

  const isLoading = isStatsLoading || isDocsLoading;

  return (
    <div className="mx-auto max-w-5xl px-5 py-10">
      {/* Header */}
      <div className="flex items-start justify-between animate-fade-up">
        <div>
          <h1 className="font-display text-3xl font-bold text-ink">
            {greeting(user?.full_name)} 👋
          </h1>
          <p className="mt-1 text-sm text-t3">Here's what's happening with your knowledge base.</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="mt-7 grid grid-cols-2 gap-4 sm:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        {isLoading ? (
          <>
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
          </>
        ) : (
          <>
            <StatCard label="Documents" value={stats?.total_documents ?? 0} icon={icons.docs} />
            <StatCard label="Conversations" value={stats?.total_chats ?? 0} icon={icons.chat} />
            <StatCard label="Storage used" value={formatBytes(stats?.storage_used_bytes ?? 0)} icon={icons.storage} accent />
          </>
        )}
      </div>

      {/* Upload zone - placed completely above list columns */}
      <div className="mt-8 animate-fade-up" style={{ animationDelay: "100ms" }}>
        <div className="mb-3">
          <h2 className="font-display text-sm font-bold text-t2 uppercase tracking-wide">Upload Documents</h2>
          <p className="text-xs text-t3 font-medium">PDF, DOCX, TXT, or Markdown — up to 25 MB. Processing runs automatically.</p>
        </div>
        <FileUploader onUpload={handleUpload} uploading={uploadMutation.isPending} />
        {error && (
          <div className="mt-3 flex items-center gap-2 rounded-xl border border-danger/20 bg-red-50 px-4 py-3 text-sm text-danger animate-fade-in">
            <svg className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}
      </div>

      {/* Lists columns */}
      <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-5">
        {/* Your documents — wider */}
        <div className="lg:col-span-3 animate-fade-up" style={{ animationDelay: "140ms" }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-ink">
              Your documents
              {documents && documents.length > 0 && (
                <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-bold text-t3">
                  {documents.length}
                </span>
              )}
            </h2>
            <div className="flex gap-3 text-xs text-t3">
              {readyCount > 0 && (
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-success" />
                  {readyCount} ready
                </span>
              )}
              {processingCount > 0 && (
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-warning animate-pulse-soft" />
                  {processingCount} processing
                </span>
              )}
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => <div key={i} className="skeleton h-16 rounded-2xl" />)}
            </div>
          ) : documents?.length ? (
            <div className="space-y-3">
              {documents.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onDelete={(id) => deleteMutation.mutate(id)} />
              ))}
            </div>
          ) : (
            <EmptyDocs />
          )}
        </div>

        {/* Recent chats — narrower */}
        <div className="lg:col-span-2 animate-fade-up" style={{ animationDelay: "180ms" }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-ink">Recent chats</h2>
            <Link to="/chat" className="text-xs font-medium text-accent hover:text-accentDark transition">New chat →</Link>
          </div>

          <div className="space-y-2">
            {conversations && conversations.length > 0 ? (
              conversations.slice(0, 6).map((c) => (
                <div key={c.id} className="group relative flex items-center justify-between rounded-2xl border border-black/5 bg-white shadow-card hover:-translate-y-0.5 hover:shadow-float hover:border-accent/20 transition duration-150">
                  <Link
                    id={`chat-link-${c.id}`}
                    to={c.document_id ? `/chat?conversationId=${c.id}&documentId=${c.document_id}` : `/chat?conversationId=${c.id}`}
                    className="flex-1 flex items-center justify-between px-4 py-3 text-sm truncate pr-16"
                  >
                    <span className="truncate text-ink group-hover:text-accent font-medium flex items-center gap-1.5 truncate">
                      {c.is_pinned && (
                        <svg className="h-3.5 w-3.5 text-accent shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.43a1 1 0 001.17-1.408l-7-14z" />
                        </svg>
                      )}
                      {c.title}
                    </span>
                    <span className="ml-2 shrink-0 text-[11px] text-t4">{timeAgo(c.created_at)}</span>
                  </Link>

                  {/* Actions overlay on hover */}
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition duration-150 z-10 bg-muted/90 rounded-lg p-0.5 shadow-sm border border-black/5">
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        pinChatMutation.mutate(c.id);
                      }}
                      className={`p-1 rounded-md transition ${
                        c.is_pinned ? "text-accent hover:bg-accent/10" : "text-t3 hover:text-ink hover:bg-black/5"
                      }`}
                      title={c.is_pinned ? "Unpin chat" : "Pin chat"}
                    >
                      <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
                      </svg>
                    </button>

                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        if (confirm("Are you sure you want to delete this chat?")) {
                          deleteChatMutation.mutate(c.id);
                        }
                      }}
                      className="p-1 rounded-md text-t3 hover:text-danger hover:bg-red-50 transition"
                      title="Delete chat"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <EmptyChats />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
