import { useState } from "react";
import { Citation } from "../types";

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "bg-success" :
    pct >= 50 ? "bg-warning" :
                "bg-danger";
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-[10px] text-t3 mb-1">
        <span>Relevance</span>
        <span className={`font-bold ${pct >= 80 ? "text-success" : pct >= 50 ? "text-warning" : "text-danger"}`}>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function CitationBadge({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);

  const label = citation.page ? `Ref Page ${citation.page}` : "Ref Doc";

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className={`mr-1 mb-1 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition cursor-default ${
          open
            ? "border-accent bg-accent text-white shadow-glow"
            : "border-accent/20 bg-accentSoft text-accent"
        }`}
      >
        <span>📄</span>
        <span className="font-display font-semibold">{label}</span>
      </button>

      {open && (
        <div className="absolute bottom-full left-0 z-30 mb-2 w-72 rounded-2xl border border-black/8 bg-white p-4 shadow-float animate-fade-up">
          {/* Source header */}
          <div className="flex items-start gap-2 border-b border-t4/40 pb-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accentSoft">
              <svg className="h-3.5 w-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-ink truncate">{citation.filename}</p>
              {citation.page && (
                <p className="text-[11px] text-t3">Page {citation.page}</p>
              )}
            </div>
          </div>

          {/* Snippet */}
          <p className="mt-3 text-xs leading-relaxed text-t2 italic">
            "{citation.snippet}"
          </p>

          {/* Confidence bar */}
          <ConfidenceBar score={citation.score} />
        </div>
      )}
    </div>
  );
}
