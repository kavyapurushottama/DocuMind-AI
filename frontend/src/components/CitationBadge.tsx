import { useState } from "react";
import { Citation } from "../types";

export default function CitationBadge({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        className="mr-1.5 mb-1.5 inline-flex items-center gap-1 rounded-full border border-accent/20 bg-accentSoft px-2.5 py-1 text-xs font-medium text-accent hover:bg-accent hover:text-white transition"
      >
        <span className="font-display">[{index + 1}]</span>
        <span className="max-w-[140px] truncate">{citation.filename}</span>
        {citation.page && <span className="opacity-70">p.{citation.page}</span>}
      </button>
      {open && (
        <div className="absolute z-10 mt-1 w-72 rounded-lg border border-black/10 bg-white p-3 text-xs text-ink/70 shadow-lg">
          <p className="mb-1 font-semibold text-ink">{citation.filename}{citation.page ? ` · page ${citation.page}` : ""}</p>
          <p className="italic">"{citation.snippet}"</p>
          <p className="mt-1 text-[10px] text-ink/40">relevance {(citation.score * 100).toFixed(0)}%</p>
        </div>
      )}
    </div>
  );
}
