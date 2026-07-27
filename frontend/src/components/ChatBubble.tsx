import { ChatMessage } from "../types";
import CitationBadge from "./CitationBadge";

export default function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[75%] ${isUser ? "order-2" : "order-1"}`}>
        <div
          className={`whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser ? "bg-accent text-white" : "bg-white border border-black/5 text-ink shadow-sm"
          }`}
        >
          {message.content}
        </div>
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 flex flex-wrap">
            {message.citations.map((c, i) => (
              <CitationBadge key={c.chunk_id} citation={c} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
