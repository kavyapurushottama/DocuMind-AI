import { ChatMessage } from "../types";
import CitationBadge from "./CitationBadge";

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex animate-fade-up ${isUser ? "justify-end" : "justify-start"}`}>
      {/* Assistant avatar */}
      {!isUser && (
        <div className="mr-2.5 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-hero-gradient shadow-sm">
          <span className="text-xs">🧠</span>
        </div>
      )}

      <div className={`max-w-[78%] space-y-2 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-accent text-white shadow-glow"
              : "bg-white border border-black/5 text-ink shadow-card"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (() => {
          const uniqueCitations = message.citations.reduce((acc: typeof message.citations, current) => {
            const isDuplicate = acc.some(
              (item) => item.filename === current.filename && item.page === current.page
            );
            if (!isDuplicate) {
              acc.push(current);
            }
            return acc;
          }, []);
          return (
            <div className="flex flex-wrap gap-1">
              {uniqueCitations.map((c, i) => (
                <CitationBadge key={c.chunk_id} citation={c} index={i} />
              ))}
            </div>
          );
        })()}

        {/* Timestamp */}
        <span className="text-[10px] text-t4 px-1">{timeAgo(message.created_at)}</span>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="ml-2.5 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-accent text-xs font-bold text-white shadow-sm">
          U
        </div>
      )}
    </div>
  );
}
