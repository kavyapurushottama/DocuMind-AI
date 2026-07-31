export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  status_detail: string | null;
  error_message: string | null;
  page_count: number | null;
  chunk_count: number;
  created_at: string;
}

export interface DashboardStats {
  total_documents: number;
  total_chats: number;
  storage_used_bytes: number;
  recent_documents: DocumentItem[];
}

export interface Citation {
  filename: string;
  page: number | null;
  chunk_id: string;
  snippet: string;
  score: number;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  document_id: string | null;
  created_at: string;
}

export interface Conversation extends ConversationSummary {
  messages: ChatMessage[];
}
