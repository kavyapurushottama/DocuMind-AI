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

function FormattedText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="space-y-1.5 leading-relaxed">
      {lines.map((line, idx) => {
        if (!line.trim()) return <div key={idx} className="h-1" />;

        const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`)/g;
        const matches = [...line.matchAll(regex)];

        if (matches.length === 0) {
          return <p key={idx}>{line}</p>;
        }

        const parts = [];
        let lastIndex = 0;
        let key = 0;

        for (const match of matches) {
          const matchIndex = match.index!;
          if (matchIndex > lastIndex) {
            parts.push(line.slice(lastIndex, matchIndex));
          }
          const raw = match[0];
          if (raw.startsWith("**") && raw.endsWith("**")) {
            parts.push(<strong key={key++} className="font-semibold">{raw.slice(2, -2)}</strong>);
          } else if (raw.startsWith("*") && raw.endsWith("*")) {
            parts.push(<em key={key++} className="italic">{raw.slice(1, -1)}</em>);
          } else if (raw.startsWith("`") && raw.endsWith("`")) {
            parts.push(<code key={key++} className="rounded bg-black/5 px-1 py-0.5 font-mono text-xs">{raw.slice(1, -1)}</code>);
          }
          lastIndex = matchIndex + raw.length;
        }
        if (lastIndex < line.length) {
          parts.push(line.slice(lastIndex));
        }

        return <p key={idx}>{parts}</p>;
      })}
    </div>
  );
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
          {isUser ? <p className="whitespace-pre-wrap">{message.content}</p> : <FormattedText text={message.content} />}
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
