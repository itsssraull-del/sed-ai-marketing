"use client";
import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api";
import { useDropzone } from "react-dropzone";
import { Database, Upload, Search, Trash2, CheckCircle, Clock } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const DOC_TYPES = ["product_catalogue","price_list","datasheet","brand_guidelines","sop","sales_script","supplier_doc","marketing_asset","company_info","misc"];

export default function KnowledgePage() {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [docType, setDocType] = useState("misc");
  const { data: stats } = useQuery({ queryKey: ["kb-stats"], queryFn: () => knowledgeApi.getStats().then(r => r.data) });
  const { data: docs } = useQuery({ queryKey: ["kb-docs"], queryFn: () => knowledgeApi.listDocuments().then(r => r.data), refetchInterval: 15_000 });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("document_type", docType);
      return knowledgeApi.upload(fd);
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["kb-docs"] }); toast.success("Document uploaded & queued for indexing"); },
    onError: () => toast.error("Upload failed"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteDocument(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["kb-docs"] }); toast.success("Document removed"); },
  });

  const onDrop = useCallback((files: File[]) => { files.forEach(f => uploadMutation.mutate(f)); }, [docType]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"], "text/plain": [".txt"], "text/csv": [".csv"] } });

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const r = await knowledgeApi.search({ query, top_k: 5 });
      setSearchResults(r.data.results);
    } catch { toast.error("Search failed"); }
    finally { setSearching(false); }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-sed-dark">Knowledge Base</h1>
        <p className="text-sed-grey-mid text-sm mt-1">RAG-powered document intelligence — {stats?.total_vectors?.toLocaleString() || 0} vectors indexed</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="card">
            <h3 className="font-semibold text-sed-dark mb-3">Upload Document</h3>
            <div className="mb-3">
              <label className="label">Document Type</label>
              <select className="input" value={docType} onChange={e => setDocType(e.target.value)}>
                {DOC_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g," ")}</option>)}
              </select>
            </div>
            <div {...getRootProps()} className={clsx("border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-colors", isDragActive ? "border-sed-orange bg-orange-50" : "border-gray-200 hover:border-sed-orange hover:bg-orange-50/30")}>
              <input {...getInputProps()} />
              <Upload size={24} className="mx-auto mb-2 text-sed-grey-mid" />
              <p className="text-sm text-sed-grey-mid">{isDragActive ? "Drop files here" : "Drag & drop or click to upload"}</p>
              <p className="text-xs text-sed-grey-light mt-1">PDF, DOCX, XLSX, TXT, CSV</p>
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-sed-dark mb-3">Stats</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-sed-grey-mid">Total Vectors</span><span className="font-bold">{stats?.total_vectors?.toLocaleString() || 0}</span></div>
              {stats?.namespaces && Object.entries(stats.namespaces).map(([ns, count]) => (
                <div key={ns} className="flex justify-between"><span className="text-sed-grey-mid capitalize">{ns}</span><span className="font-medium">{count as number}</span></div>
              ))}
            </div>
          </div>
        </div>
        <div className="lg:col-span-2 space-y-4">
          <div className="card">
            <h3 className="font-semibold text-sed-dark mb-3">Semantic Search</h3>
            <div className="flex gap-2">
              <input className="input flex-1" placeholder="Search the knowledge base..." value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSearch()} />
              <button className="btn-primary px-4" onClick={handleSearch} disabled={searching}>{searching ? "..." : <Search size={15} />}</button>
            </div>
            {searchResults.length > 0 && (
              <div className="mt-4 space-y-3">
                {searchResults.map((r,i) => (
                  <div key={i} className="bg-gray-50 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-sed-orange">{r.document_type}</span>
                      <span className="text-xs text-sed-grey-mid">Score: {(r.score*100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm text-sed-grey line-clamp-3">{r.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="card">
            <h3 className="font-semibold text-sed-dark mb-3">Indexed Documents ({docs?.length || 0})</h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {docs?.map((doc: any) => (
                <div key={doc.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 group">
                  {doc.is_indexed ? <CheckCircle size={15} className="text-green-500 flex-shrink-0"/> : <Clock size={15} className="text-yellow-500 flex-shrink-0"/>}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{doc.title}</p>
                    <p className="text-xs text-sed-grey-mid">{doc.doc_type.replace(/_/g," ")} · {doc.chunk_count} chunks · {doc.file_size_bytes ? `${(doc.file_size_bytes/1024).toFixed(0)}KB` : ""}</p>
                  </div>
                  <button className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 rounded-lg text-red-400 transition-all" onClick={() => deleteMutation.mutate(doc.id)}>
                    <Trash2 size={13}/>
                  </button>
                </div>
              ))}
              {(!docs || docs.length === 0) && <p className="text-sm text-sed-grey-mid text-center py-6">No documents uploaded yet</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
