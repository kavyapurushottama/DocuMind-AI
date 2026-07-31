import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteDocument, listDocuments, uploadDocument } from "../api/documents";
import FileUploader from "../components/FileUploader";
import DocumentCard from "../components/DocumentCard";

export default function UploadPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      const docs = query.state.data as Awaited<ReturnType<typeof listDocuments>> | undefined;
      const stillWorking = docs?.some((d) => d.status === "pending" || d.status === "processing");
      return stillWorking ? 2000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setError("");
    },
    onError: (err: any) => setError(err?.response?.data?.detail || "Upload failed. Please try again."),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const handleUpload = (file: File) => {
    setError("");
    uploadMutation.mutate(file);
  };

  const readyCount     = documents?.filter((d) => d.status === "ready").length ?? 0;
  const processingCount = documents?.filter((d) => d.status === "processing" || d.status === "pending").length ?? 0;

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      {/* Header */}
      <div className="animate-fade-up">
        <h1 className="font-display text-3xl font-bold text-ink">Upload documents</h1>
        <p className="mt-1 text-sm text-t3">
          PDF, DOCX, TXT, or Markdown — up to 25 MB each. Processing runs automatically.
        </p>
      </div>

      {/* Upload zone */}
      <div className="mt-6 animate-fade-up" style={{ animationDelay: "60ms" }}>
        <FileUploader onUpload={handleUpload} uploading={uploadMutation.isPending} />
        {error && (
          <div className="mt-3 flex items-center gap-2 rounded-xl border border-danger/20 bg-red-50 px-4 py-3 text-sm text-danger animate-fade-in">
            <svg className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}
      </div>

      {/* Document list */}
      <div className="mt-10 animate-fade-up" style={{ animationDelay: "120ms" }}>
        {/* Summary strip */}
        {(documents?.length ?? 0) > 0 && (
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-ink">
              Your documents
              <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-bold text-t3">
                {documents!.length}
              </span>
            </h2>
            <div className="flex gap-3 text-xs text-t3">
              {readyCount > 0 && (
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-success" />
                  {readyCount} ready
                </span>
              )}
              {processingCount > 0 && (
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-warning animate-pulse-soft" />
                  {processingCount} processing
                </span>
              )}
            </div>
          </div>
        )}

        {/* Cards */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="skeleton h-16 rounded-2xl" />)}
          </div>
        ) : documents?.length ? (
          <div className="space-y-3">
            {documents.map((doc, i) => (
              <div key={doc.id} className="animate-fade-up" style={{ animationDelay: `${i * 40}ms` }}>
                <DocumentCard doc={doc} onDelete={(id) => deleteMutation.mutate(id)} />
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-t4/60 bg-white py-16 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accentSoft">
              <svg className="h-7 w-7 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-ink">No documents yet</p>
            <p className="mt-1 text-xs text-t3">Upload your first file above to get started</p>
          </div>
        )}
      </div>
    </div>
  );
}
