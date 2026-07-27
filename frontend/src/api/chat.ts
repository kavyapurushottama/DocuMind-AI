import { apiClient } from "./client";
import { Conversation, ConversationSummary, ChatMessage } from "../types";

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

export async function listConversations(): Promise<ConversationSummary[]> {
  const { data } = await apiClient.get("/api/chat/conversations");
  return data;
}

export async function getConversation(id: string): Promise<Conversation> {
  const { data } = await apiClient.get(`/api/chat/conversations/${id}`);
  return data;
}
