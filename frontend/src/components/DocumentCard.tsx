import { Link } from "react-router-dom";
import { DocumentItem } from "../types";

const STATUS_STYLES: Record<string, string> = {
  ready: "bg-green-100 text-green-700",
  processing: "bg-amber-100 text-amber-700",
  pending: "bg-gray-100 text-gray-600",
  failed: "bg-red-100 text-red-700",
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentCard({ doc, onDelete }: { doc: DocumentItem; onDelete?: (id: string) => void }) {
  return (
    <div className="group flex items-center justify-between rounded-xl border border-black/5 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-display text-sm font-semibold text-ink">{doc.filename}</span>
          <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_STYLES[doc.status]}`}>
            {doc.status}
          </span>
        </div>
        <p className="mt-1 text-xs text-ink/50">
          {doc.file_type.toUpperCase()} · {formatBytes(doc.file_size_bytes)}
          {doc.page_count ? ` · ${doc.page_count} pages` : ""} · {doc.chunk_count} chunks
        </p>
        {doc.status === "failed" && doc.error_message && (
          <p className="mt-1 text-xs text-red-500">{doc.error_message}</p>
        )}
      </div>
      <div className="ml-4 flex shrink-0 items-center gap-2">
        {doc.status === "ready" && (
          <Link
            to={`/chat?documentId=${doc.id}`}
            className="rounded-lg bg-accentSoft px-3 py-1.5 text-xs font-medium text-accent hover:bg-accent hover:text-white transition"
          >
            Chat
          </Link>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(doc.id)}
            className="rounded-lg px-2 py-1.5 text-xs text-ink/40 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
