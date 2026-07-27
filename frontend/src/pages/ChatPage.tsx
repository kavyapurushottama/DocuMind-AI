import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { askQuestion, getConversation } from "../api/chat";
import { listDocuments } from "../api/documents";
import ChatBubble from "../components/ChatBubble";
import { ChatMessage } from "../types";

const QUICK_ACTIONS = ["Summarize this", "Explain this", "Find key points", "Generate interview questions"];

export default function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const documentId = searchParams.get("documentId");
  const conversationIdParam = searchParams.get("conversationId");

  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState<string | null>(conversationIdParam);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: documents } = useQuery({ queryKey: ["documents"], queryFn: listDocuments });
  const readyDocs = documents?.filter((d) => d.status === "ready") ?? [];

  useEffect(() => {
    if (conversationIdParam) {
      getConversation(conversationIdParam).then((c) => {
        setConversationId(c.id);
        setMessages(c.messages);
      });
    }
  }, [conversationIdParam]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askMutation = useMutation({
    mutationFn: (question: string) => askQuestion({ question, documentId, conversationId }),
    onMutate: (question: string) => {
      const tempUserMsg: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: question,
        citations: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);
    },
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      setMessages((prev) => [...prev, data.message]);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      if (!conversationIdParam) {
        setSearchParams((prev) => {
          prev.set("conversationId", data.conversation_id);
          return prev;
        });
      }
    },
  });

  const handleSend = (text?: string) => {
    const question = (text ?? input).trim();
    if (!question || askMutation.isPending) return;
    setInput("");
    askMutation.mutate(question);
  };

  const activeDoc = readyDocs.find((d) => d.id === documentId);

  return (
    <div className="mx-auto flex h-[calc(100vh-64px)] max-w-3xl flex-col px-6">
      <div className="border-b border-black/5 py-4">
        <h1 className="font-display text-lg font-semibold text-ink">
          {activeDoc ? `Chat · ${activeDoc.filename}` : "Chat across all documents"}
        </h1>
        <select
          value={documentId ?? ""}
          onChange={(e) => {
            const val = e.target.value;
            setSearchParams(val ? { documentId: val } : {});
            setConversationId(null);
            setMessages([]);
          }}
          className="mt-2 rounded-lg border border-black/10 px-2 py-1 text-xs text-ink/70"
        >
          <option value="">All documents</option>
          {readyDocs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.filename}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto py-6">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <p className="text-sm text-ink/40">Ask anything about your document(s).</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action}
                  onClick={() => handleSend(action)}
                  className="rounded-full border border-black/10 px-3 py-1.5 text-xs text-ink/60 hover:border-accent hover:text-accent transition"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}
        {askMutation.isPending && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-black/5 bg-white px-4 py-3 text-sm text-ink/40 shadow-sm">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2 border-t border-black/5 py-4"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents..."
          className="flex-1 rounded-lg border border-black/10 px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={askMutation.isPending}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent/90 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
