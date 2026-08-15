import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { askQuestion, getConversation, listConversations, deleteConversation, pinConversation } from "../api/chat";
import { listDocuments, downloadDocument } from "../api/documents";
import { apiClient } from "../api/client";
// @ts-ignore
import { renderAsync } from "docx-preview";
import ChatBubble from "../components/ChatBubble";
import { ChatMessage, ConversationSummary } from "../types";

const QUICK_ACTIONS = [
  { label: "Summarize this document",       emoji: "📝" },
  { label: "Explain the key concepts",       emoji: "💡" },
  { label: "Find the main conclusions",      emoji: "🎯" },
  { label: "Generate interview questions",   emoji: "🎤" },
];

function ThinkingDots() {
  return (
    <div className="flex justify-start animate-fade-in">
      <div className="mr-2.5 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-hero-gradient shadow-sm">
        <span className="text-xs">🧠</span>
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-card">
        <span className="h-2 w-2 rounded-full bg-accent dot-1" />
        <span className="h-2 w-2 rounded-full bg-accent dot-2" />
        <span className="h-2 w-2 rounded-full bg-accent dot-3" />
      </div>
    </div>
  );
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

function ConversationItem({
  c,
  active,
  onClick,
  onPin,
  onDelete,
}: {
  c: ConversationSummary;
  active: boolean;
  onClick: () => void;
  onPin: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="group relative flex items-center justify-between rounded-xl hover:bg-muted transition">
      <button
        onClick={onClick}
        className={`flex-1 rounded-xl px-3 py-2.5 text-left transition truncate pr-14 ${
          active ? "bg-accentSoft text-accent" : "text-t2 hover:text-ink"
        }`}
      >
        <div className="flex items-center gap-1.5 truncate">
          {c.is_pinned && (
            <svg className="h-3.5 w-3.5 text-accent shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.43a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          )}
          <p className="truncate text-xs font-semibold">{c.title}</p>
        </div>
        <p className="mt-0.5 text-[10px] text-t4">{timeAgo(c.created_at)}</p>
      </button>

      {/* Hover actions */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition duration-150 z-10 bg-muted/80 rounded-lg p-0.5 shadow-sm border border-black/5">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPin();
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
            e.stopPropagation();
            if (confirm("Are you sure you want to delete this chat?")) {
              onDelete();
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
  );
}

interface DocumentViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeDoc: { id: string; filename: string } | null;
}

function DocumentViewerModal({ isOpen, onClose, activeDoc }: DocumentViewerModalProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [docxBlob, setDocxBlob] = useState<Blob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const docxContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && activeDoc) {
      setLoading(true);
      setError(false);
      setDocxBlob(null);

      apiClient.get(`/api/documents/${activeDoc.id}/download`, { responseType: 'blob' })
        .then(response => {
          const fileExt = activeDoc.filename.toLowerCase().split('.').pop() || '';
          const contentType = response.headers['content-type'] ? String(response.headers['content-type']) : undefined;
          const blob = new Blob([response.data], { type: contentType });
          
          if (fileExt === 'docx') {
            setDocxBlob(blob);
          } else {
            const url = URL.createObjectURL(blob);
            setPreviewUrl(url);
          }
        })
        .catch(err => {
          console.error("Failed to load document preview", err);
          setError(true);
        })
        .finally(() => {
          setLoading(false);
        });
    }

    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
      setDocxBlob(null);
    };
  }, [isOpen, activeDoc]);

  useEffect(() => {
    if (docxBlob && docxContainerRef.current) {
      docxContainerRef.current.innerHTML = ""; // Clear previous render
      renderAsync(docxBlob, docxContainerRef.current, undefined, {
        className: "docx-preview-container",
        inWrapper: false
      }).catch(err => {
        console.error("Failed to render DOCX", err);
        setError(true);
      });
    }
  }, [docxBlob]);

  if (!isOpen || !activeDoc) return null;

  const fileExt = activeDoc.filename.toLowerCase().split('.').pop() || '';
  const isDocx = fileExt === 'docx';

  const handleDownload = () => {
    downloadDocument(activeDoc.id, activeDoc.filename);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative flex h-[85vh] w-full max-w-4xl flex-col rounded-3xl bg-white border border-black/5 shadow-glow-lg overflow-hidden animate-fade-up">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-black/5 px-6 py-4 bg-muted/40">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-sm font-semibold text-ink truncate max-w-[500px]">{activeDoc.filename}</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="rounded-xl p-2 text-t3 hover:bg-black/5 hover:text-ink transition"
              title="Download original file"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="rounded-xl p-2 text-t3 hover:bg-black/5 hover:text-ink transition"
              title="Close viewer"
            >
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Viewer Body */}
        <div className="flex-1 overflow-auto p-6 bg-muted/20">
          {loading ? (
            <div className="flex h-full flex-col items-center justify-center">
              <span className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
              <p className="mt-3 text-sm text-t3">Loading document preview...</p>
            </div>
          ) : error ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 text-danger">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-sm font-semibold text-ink">Failed to load preview</p>
              <p className="mt-1 text-xs text-t3">Please download the file to view its contents.</p>
              <button
                onClick={handleDownload}
                className="mt-4 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white transition hover:bg-accentDark shadow"
              >
                Download Document
              </button>
            </div>
          ) : isDocx ? (
            <div className="w-full min-h-full rounded-2xl border border-black/5 bg-white p-6 shadow-card overflow-auto">
              <div ref={docxContainerRef} className="docx-render-container flex flex-col items-center justify-start [&_.docx-preview-container]:max-w-full" />
            </div>
          ) : previewUrl ? (
            <iframe
              src={previewUrl}
              className="h-full w-full rounded-2xl border border-black/5 bg-white shadow-card"
              title={activeDoc.filename}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const documentId     = searchParams.get("documentId");
  const convIdParam    = searchParams.get("conversationId");

  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState<string | null>(convIdParam);
  const [messages, setMessages]             = useState<ChatMessage[]>([]);
  const [input, setInput]                   = useState("");
  const [sidebarOpen, setSidebarOpen]       = useState(true);
  const [viewerOpen, setViewerOpen]         = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLTextAreaElement>(null);

  const { data: documents }     = useQuery({ queryKey: ["documents"],     queryFn: listDocuments });
  const { data: conversations } = useQuery({ queryKey: ["conversations"], queryFn: listConversations });
  const readyDocs = documents?.filter((d) => d.status === "ready") ?? [];
  const activeDoc = readyDocs.find((d) => d.id === documentId);

  /* Load conversation on URL param change */
  useEffect(() => {
    if (convIdParam) {
      getConversation(convIdParam).then((c) => {
        setConversationId(c.id);
        setMessages(c.messages);
      });
    } else {
      setMessages([]);
      setConversationId(null);
    }
  }, [convIdParam]);

  /* Scroll to bottom on new messages */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askMutation = useMutation({
    mutationFn: (question: string) =>
      askQuestion({ question, documentId, conversationId }),
    onMutate: (question: string) => {
      const tempMsg: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: question,
        citations: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempMsg]);
    },
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      setMessages((prev) => [...prev, data.message]);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      if (convIdParam !== data.conversation_id) {
        setSearchParams((p) => {
          const next = new URLSearchParams(p);
          next.set("conversationId", data.conversation_id);
          if (documentId) next.set("documentId", documentId);
          return next;
        });
      }
    },
    onError: (err: any) => {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: err?.response?.data?.detail || "Could not reach the AI response service. Please check your backend connection.",
        citations: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSearchParams({});
      setMessages([]);
      setConversationId(null);
    },
  });

  const pinChatMutation = useMutation({
    mutationFn: pinConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const handleSend = (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || askMutation.isPending) return;
    setInput("");
    askMutation.mutate(q);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-[calc(100vh-56px)] overflow-hidden">

      {/* ─── Sidebar ─── */}
      <aside
        className={`flex flex-col border-r border-black/5 bg-white transition-all duration-300 ${
          sidebarOpen ? "w-56 opacity-100" : "w-0 opacity-0 overflow-hidden"
        }`}
      >
        <div className="flex items-center justify-between border-b border-black/5 px-3 py-3">
          <span className="text-xs font-semibold text-t2 uppercase tracking-wide">Chats</span>
          <button
            id="new-chat-btn"
            onClick={() => { setSearchParams({}); setMessages([]); setConversationId(null); }}
            className="rounded-lg p-1 text-t3 hover:bg-accentSoft hover:text-accent transition"
            title="New chat"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {conversations?.map((c) => (
            <ConversationItem
              key={c.id}
              c={c}
              active={c.id === conversationId}
              onClick={() => setSearchParams(c.document_id ? { conversationId: c.id, documentId: c.document_id } : { conversationId: c.id })}
              onPin={() => pinChatMutation.mutate(c.id)}
              onDelete={() => deleteChatMutation.mutate(c.id)}
            />
          ))}
          {!conversations?.length && (
            <p className="px-3 py-4 text-[11px] text-t4 text-center">No chats yet</p>
          )}
        </div>
      </aside>

      {/* ─── Main area ─── */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Top bar */}
        <div className="flex items-center gap-3 border-b border-black/5 bg-white px-4 py-2.5">
          {/* Sidebar toggle */}
          <button
            id="sidebar-toggle"
            onClick={() => setSidebarOpen((v) => !v)}
            className="rounded-lg p-1.5 text-t3 hover:bg-muted hover:text-ink transition"
            title="Toggle sidebar"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Context chip - click triggers preview modal */}
          {activeDoc ? (
            <div className="flex items-center gap-1 rounded-full bg-accentSoft border border-accent/15 p-0.5 pr-2">
              <button
                onClick={() => setViewerOpen(true)}
                className="flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold text-accent hover:bg-accent/10 transition cursor-pointer"
                title="View original document in popup"
              >
                <svg className="h-3 w-3 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span className="truncate max-w-[200px] hover:underline">{activeDoc.filename}</span>
              </button>
              
              <button
                onClick={() => setSearchParams({})}
                className="text-accent/60 hover:text-accent p-0.5 rounded-full hover:bg-accent/10 transition"
                title="Clear context filter"
              >
                <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                </svg>
              </button>
            </div>
          ) : (
            <span className="text-sm text-t3 font-medium">All documents</span>
          )}

          {/* Doc picker */}
          <select
            id="doc-picker"
            value={documentId ?? ""}
            onChange={(e) => {
              const val = e.target.value;
              setSearchParams(val ? { documentId: val } : {});
              setConversationId(null);
              setMessages([]);
            }}
            className="ml-auto rounded-xl border border-t4/60 bg-white px-2.5 py-1.5 text-xs text-t2 focus:border-accent"
          >
            <option value="">All documents</option>
            {readyDocs.map((d) => (
              <option key={d.id} value={d.id}>{d.filename}</option>
            ))}
          </select>
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-6">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center animate-fade-in">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-hero-gradient shadow-glow-lg">
                <span className="text-3xl">🧠</span>
              </div>
              <h2 className="font-display text-lg font-bold text-ink">Ask DocuMind AI</h2>
              <p className="mt-1 text-sm text-t3">
                {activeDoc ? `Chatting with "${activeDoc.filename}"` : "Ask anything across all your documents"}
              </p>

              <div className="mt-6 grid grid-cols-2 gap-2 max-w-md">
                {QUICK_ACTIONS.map((a) => (
                  <button
                    key={a.label}
                    onClick={() => handleSend(a.label)}
                    className="flex items-center gap-2 rounded-xl border border-black/7 bg-white px-3 py-2.5 text-left text-xs text-t2 shadow-card transition hover:border-accent/30 hover:bg-accentSoft hover:text-accent hover:-translate-y-0.5 hover:shadow-float"
                  >
                    <span>{a.emoji}</span>
                    <span className="font-medium">{a.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <ChatBubble key={m.id} message={m} />
          ))}

          {askMutation.isPending && <ThinkingDots />}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-black/5 bg-white px-4 py-3">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex items-end gap-2"
            id="chat-form"
          >
            <textarea
              ref={inputRef}
              id="chat-input"
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents…"
              className="flex-1 resize-none rounded-xl border border-t4/60 bg-muted px-4 py-2.5 text-sm text-ink placeholder-t4 transition hover:border-accent/40 focus:border-accent focus:bg-white"
              style={{ maxHeight: "140px" }}
            />
            <button
              id="chat-send-btn"
              type="submit"
              disabled={askMutation.isPending || !input.trim()}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-white shadow transition hover:bg-accentDark hover:shadow-glow disabled:cursor-not-allowed disabled:opacity-40"
              title="Send (Enter)"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
          <p className="mt-1.5 text-center text-[10px] text-t4">
            Press <kbd className="rounded border border-t4/60 px-1 font-mono">Enter</kbd> to send · <kbd className="rounded border border-t4/60 px-1 font-mono">Shift+Enter</kbd> for newline
          </p>
        </div>
      </div>
      
      {/* Document Viewer Modal */}
      <DocumentViewerModal
        isOpen={viewerOpen}
        onClose={() => setViewerOpen(false)}
        activeDoc={activeDoc ?? null}
      />
    </div>
  );
}
