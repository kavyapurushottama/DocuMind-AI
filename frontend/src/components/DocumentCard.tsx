import { Link } from "react-router-dom";
import { DocumentItem } from "../types";

/* ─── Status config ─── */
const STATUS_CONFIG = {
  ready:      { dot: "bg-success",  pill: "bg-green-50  text-success",   label: "Ready" },
  processing: { dot: "bg-warning",  pill: "bg-amber-50  text-warning",   label: "Processing" },
  pending:    { dot: "bg-t4",       pill: "bg-muted     text-t3",        label: "Pending" },
  failed:     { dot: "bg-danger",   pill: "bg-red-50    text-danger",    label: "Failed" },
};

/* ─── File type config ─── */
const FILE_CONFIG: Record<string, { bg: string; color: string }> = {
  pdf:  { bg: "bg-red-50",    color: "text-danger"  },
  docx: { bg: "bg-blue-50",   color: "text-blue-600" },
  txt:  { bg: "bg-gray-100",  color: "text-t2"       },
  md:   { bg: "bg-violet-50", color: "text-violet"   },
};

function FileIcon({ type }: { type: string }) {
  const { bg, color } = FILE_CONFIG[type] ?? FILE_CONFIG.txt;
  return (
    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${bg}`}>
      <span className={`text-[10px] font-extrabold tracking-tight ${color}`}>
        {type.toUpperCase().slice(0, 4)}
      </span>
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentCard({
  doc,
  onDelete,
}: {
  doc: DocumentItem;
  onDelete?: (id: string) => void;
}) {
  const s = STATUS_CONFIG[doc.status] ?? STATUS_CONFIG.pending;

  return (
    <div
      id={`doc-card-${doc.id}`}
      className="group flex items-center gap-3 rounded-2xl border border-black/5 bg-white p-3.5 shadow-card transition hover:-translate-y-0.5 hover:shadow-float hover:border-accent/15"
    >
      <FileIcon type={doc.file_type} />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-display text-sm font-semibold text-ink">{doc.filename}</span>
          <span className={`flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${s.pill}`}>
            {doc.status === "processing" && (
              <span className={`h-1.5 w-1.5 rounded-full ${s.dot} animate-pulse-soft`} />
            )}
            {doc.status !== "processing" && (
              <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
            )}
            {s.label}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-t3">
          {doc.status === "processing" && doc.status_detail ? (
            <span className="flex items-center gap-1.5 text-accent font-medium animate-pulse-soft">
              <span className="relative flex h-1.5 w-1.5 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-accent"></span>
              </span>
              {doc.status_detail}
            </span>
          ) : (
            <>
              {formatBytes(doc.file_size_bytes)}
              {doc.page_count ? ` · ${doc.page_count} pages` : ""}
              {doc.chunk_count ? ` · ${doc.chunk_count} chunks` : ""}
            </>
          )}
        </p>
        {doc.status === "failed" && doc.error_message && (
          <p className="mt-1 text-xs text-danger">{doc.error_message}</p>
        )}
      </div>

      {/* Actions — always visible */}
      <div className="flex shrink-0 items-center gap-1.5">
        {doc.status === "ready" && (
          <Link
            to={`/chat?documentId=${doc.id}`}
            id={`doc-chat-${doc.id}`}
            className="flex items-center gap-1 rounded-xl bg-accentSoft px-3 py-1.5 text-xs font-semibold text-accent transition hover:bg-accent hover:text-white"
          >
            Chat
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        )}
        {onDelete && (
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
                onDelete(doc.id);
              }
            }}
            id={`doc-delete-${doc.id}`}
            className="flex items-center justify-center rounded-xl p-2 text-t3 transition hover:bg-red-50 hover:text-danger hover:scale-105"
            title="Delete document"
            aria-label="Delete document"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
