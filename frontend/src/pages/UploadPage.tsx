import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteDocument, listDocuments, uploadDocument } from "../api/documents";
import FileUploader from "../components/FileUploader";
import DocumentCard from "../components/DocumentCard";

export default function UploadPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    // poll while anything is still processing so status updates show up live
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
    },
    onError: (err: any) => setError(err?.response?.data?.detail || "Upload failed"),
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

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="font-display text-2xl font-bold text-ink">Upload documents</h1>
      <p className="mt-1 text-sm text-ink/50">PDF, DOCX, TXT, or Markdown. Processing runs automatically.</p>

      <div className="mt-6">
        <FileUploader onUpload={handleUpload} uploading={uploadMutation.isPending} />
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </div>

      <div className="mt-10 space-y-3">
        {documents?.length ? (
          documents.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} onDelete={(id) => deleteMutation.mutate(id)} />
          ))
        ) : (
          <p className="text-sm text-ink/40">No documents uploaded yet.</p>
        )}
      </div>
    </div>
  );
}
