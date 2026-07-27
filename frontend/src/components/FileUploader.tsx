import { useCallback, useRef, useState } from "react";

const ACCEPTED = ".pdf,.docx,.txt,.md";

export default function FileUploader({
  onUpload,
  uploading,
}: {
  onUpload: (file: File) => void;
  uploading: boolean;
}) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      onUpload(files[0]);
    },
    [onUpload]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition ${
        dragOver ? "border-accent bg-accentSoft" : "border-black/10 bg-white hover:border-accent/40"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="font-display text-lg font-semibold text-ink">
        {uploading ? "Uploading..." : "Drop a document here"}
      </div>
      <p className="mt-1 text-sm text-ink/50">or click to browse — PDF, DOCX, TXT, or Markdown</p>
    </div>
  );
}
