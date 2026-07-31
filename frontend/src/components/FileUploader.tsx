import { useCallback, useRef, useState } from "react";

const ACCEPTED = ".pdf,.docx,.txt,.md";

const FILE_ICONS: Record<string, { bg: string; color: string; label: string }> = {
  pdf:  { bg: "bg-red-50",   color: "text-danger",  label: "PDF"  },
  docx: { bg: "bg-blue-50",  color: "text-blue-600", label: "DOCX" },
  txt:  { bg: "bg-gray-50",  color: "text-t2",       label: "TXT"  },
  md:   { bg: "bg-violet-50",color: "text-violet",   label: "MD"   },
};

function UploadIcon() {
  return (
    <svg className="h-10 w-10 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
  );
}

export default function FileUploader({
  onUpload,
  uploading,
}: {
  onUpload: (file: File) => void;
  uploading: boolean;
}) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<{ name: string; ext: string; size: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const formatBytes = (b: number) => {
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
      setPreview({ name: file.name, ext, size: formatBytes(file.size) });
      onUpload(file);
    },
    [onUpload]
  );

  const fileStyle = FILE_ICONS[preview?.ext ?? ""] ?? FILE_ICONS.txt;

  return (
    <div
      id="file-drop-zone"
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-3xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
        dragOver
          ? "border-accent bg-accentSoft scale-[1.01] shadow-glow"
          : "border-t4/60 bg-white hover:border-accent/50 hover:bg-accentSoft/30"
      }`}
    >
      {/* Subtle background blob */}
      <div className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-accent/5 blur-2xl" />

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-3 animate-fade-in">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accentSoft">
            <svg className="h-7 w-7 text-accent animate-spin-slow" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
            </svg>
          </div>
          {preview && (
            <div className={`flex items-center gap-2 rounded-xl px-3 py-1.5 ${fileStyle.bg}`}>
              <span className={`text-xs font-bold ${fileStyle.color}`}>{fileStyle.label}</span>
              <span className="text-xs text-t2 truncate max-w-[200px]">{preview.name}</span>
              <span className="text-[10px] text-t4">{preview.size}</span>
            </div>
          )}
          <p className="text-sm font-medium text-accent">Uploading &amp; processing…</p>
          <p className="text-xs text-t3">This may take a moment</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div className={`flex h-14 w-14 items-center justify-center rounded-2xl transition-transform duration-200 ${dragOver ? "bg-accent scale-110" : "bg-accentSoft"}`}>
            {dragOver ? (
              <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            ) : (
              <UploadIcon />
            )}
          </div>

          <div>
            <p className="font-display text-base font-semibold text-ink">
              {dragOver ? "Drop to upload" : "Drop your document here"}
            </p>
            <p className="mt-1 text-sm text-t3">or <span className="text-accent font-medium">click to browse</span></p>
          </div>

          {/* Accepted types */}
          <div className="mt-2 flex flex-wrap justify-center gap-1.5">
            {["PDF", "DOCX", "TXT", "MD"].map((t) => (
              <span key={t} className="rounded-lg border border-t4/60 bg-muted px-2 py-0.5 text-[11px] font-semibold text-t3">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
