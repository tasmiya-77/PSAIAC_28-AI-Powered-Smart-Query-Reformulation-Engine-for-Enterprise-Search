"use client";

import React, { useState, useEffect } from "react";
import { UploadCloud, FileText, Trash2, Database, RefreshCw } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/context/ToastContext";
import { apiClient } from "@/lib/api-client";
import { DocumentListItem } from "@/types/api";

export const UploadContainer: React.FC = () => {
  const { success, error: toastError } = useToast();
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

  const fetchDocuments = async () => {
    setIsFetching(true);
    try {
      const data = await apiClient.getDocuments();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch {
      // Backend status fallback
    } finally {
      setIsFetching(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);

    try {
      const data = await apiClient.uploadDocument(file);
      success("Document Ingested", data.message);
      fetchDocuments();
    } catch (err: any) {
      toastError("Upload Error", err.message || "Failed to upload document.");
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await apiClient.deleteDocument(docId);
      success("Document Deleted", `Removed document ${docId} from ChromaDB.`);
      fetchDocuments();
    } catch (err: any) {
      toastError("Delete Error", err.message);
    }
  };

  return (
    <div className="space-y-6 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <UploadCloud className="h-6 w-6 text-indigo-500" />
            Knowledge Base Ingestion
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Upload PDF, DOCX, TXT, or Markdown documents to chunk and embed into ChromaDB vector store.
          </p>
        </div>
        <Badge variant="default">ChromaDB Store</Badge>
      </div>

      {/* Drag & Drop Card */}
      <Card variant="glass" className="border-dashed border-2 border-slate-300 dark:border-slate-800 text-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500">
            <UploadCloud className={`h-6 w-6 ${isUploading ? "animate-bounce" : ""}`} />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Drag & Drop file or click to upload
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Supports PDF, DOCX, TXT, MD (Max 25MB per file) • SHA-256 Duplicate Check Active
            </div>
          </div>

          <label
            aria-label="Upload document file"
            className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all"
          >
            <span>Select File</span>
            <input type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt,.md" className="hidden" disabled={isUploading} />
          </label>
        </div>
      </Card>

      {/* Ingested Documents List */}
      <Card variant="glass">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Database className="h-4 w-4 text-indigo-400" />
              Ingested Vector Documents
            </CardTitle>
            <CardDescription className="text-xs">
              Total {documents.length} documents ({totalChunks} vector chunks indexed)
            </CardDescription>
          </div>
          <button
            onClick={fetchDocuments}
            aria-label="Refresh document list"
            className="p-1.5 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          </button>
        </CardHeader>

        <CardContent className="pt-2">
          {documents.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">
              No documents ingested yet. Upload your first document above.
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div key={doc.document_id} className="flex items-center justify-between p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-900/40 text-xs">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-800 dark:text-slate-200">{doc.filename}</div>
                      <div className="text-[11px] text-slate-500">
                        {doc.file_type.toUpperCase()} • {doc.chunk_count} Chunks • Uploaded {doc.upload_date.slice(0, 10)}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.document_id)}
                    aria-label={`Delete ${doc.filename}`}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-slate-800 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
