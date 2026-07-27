import { apiClient } from "./client";
import { DashboardStats, DocumentItem } from "../types";

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const { data } = await apiClient.get("/api/documents");
  return data;
}

export async function getDocument(id: string): Promise<DocumentItem> {
  const { data } = await apiClient.get(`/api/documents/${id}`);
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/documents/${id}`);
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get("/api/documents/dashboard/stats");
  return data;
}
