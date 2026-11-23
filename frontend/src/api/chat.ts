import { apiClient } from "./client";
import { Conversation, ConversationSummary, ChatMessage, Citation } from "../types";

export async function askQuestion(params: {
  question: string;
  documentId?: string | null;
  conversationId?: string | null;
}): Promise<{ conversation_id: string; message: ChatMessage }> {
  const { data } = await apiClient.post("/api/chat/ask", {
    question: params.question,
    document_id: params.documentId || null,
    conversation_id: params.conversationId || null,
  });
  return data;
}

export async function askQuestionStream(
  params: {
    question: string;
    documentId?: string | null;
    conversationId?: string | null;
  },
  callbacks: {
    onMetadata?: (meta: { conversation_id: string }) => void;
    onCitations?: (citations: Citation[]) => void;
    onToken?: (token: string) => void;
    onDone?: () => void;
    onError?: (err: Error) => void;
  }
): Promise<void> {
  const token = localStorage.getItem("token");
  // Default to window.location.origin or configured API url
  const apiBase = import.meta.env.VITE_API_URL || (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");
  const url = `${apiBase.replace(/\/+$/, "")}/api/chat/ask/stream`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question: params.question,
      document_id: params.documentId || null,
      conversation_id: params.conversationId || null,
    }),
  });

  if (!response.ok) {
    let msg = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      msg = errJson.detail || msg;
    } catch {}
    const err = new Error(msg);
    callbacks.onError?.(err);
    throw err;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("ReadableStream not supported on this browser.");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const chunk of parts) {
      const trimmed = chunk.trim();
      if (!trimmed || !trimmed.startsWith("data:")) continue;
      const dataStr = trimmed.slice(5).trim();

      if (dataStr === "[DONE]") {
        callbacks.onDone?.();
        return;
      }

      try {
        const payload = JSON.parse(dataStr);
        if (payload.type === "metadata" && callbacks.onMetadata) {
          callbacks.onMetadata({ conversation_id: payload.conversation_id });
        } else if (payload.type === "citations" && callbacks.onCitations) {
          callbacks.onCitations(payload.citations);
        } else if (payload.type === "token" && callbacks.onToken) {
          callbacks.onToken(payload.content);
        }
      } catch (e) {
        console.warn("Failed to parse SSE line", dataStr, e);
      }
    }
  }

  callbacks.onDone?.();
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const { data } = await apiClient.get("/api/chat/conversations");
  return data;
}

export async function getConversation(id: string): Promise<Conversation> {
  const { data } = await apiClient.get(`/api/chat/conversations/${id}`);
  return data;
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/api/chat/conversations/${id}`);
}

export async function pinConversation(id: string): Promise<{ is_pinned: boolean }> {
  const { data } = await apiClient.post(`/api/chat/conversations/${id}/pin`);
  return data;
}
