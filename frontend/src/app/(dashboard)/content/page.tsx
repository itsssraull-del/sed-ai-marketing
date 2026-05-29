"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { contentApi, socialApi } from "@/lib/api";
import { Zap, Check, X, Eye, Clock, Send, RefreshCw, Plus, ChevronDown } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const PLATFORMS = ["facebook", "instagram", "linkedin", "whatsapp"];
const CONTENT_TYPES = ["text_post", "image_post", "carousel", "video", "reel", "story", "article"];
const TOPICS = [
  "stock_arrival", "educational", "promotional", "industry_news", "thought_leadership",
  "installer_tip", "battery_knowledge", "inverter_guide", "solar_myth_busting",
  "loadshedding_update", "c_and_i_insight", "company_announcement"
];
const AUDIENCES = ["solar installers", "epc contractors", "commercial buyers", "project developers", "resellers"];

const STATUS_BADGE: Record<string, string> = {
  draft:           "badge-gray",
  pending_review:  "badge-yellow",
  approved:        "badge-green",
  scheduled:       "badge-blue",
  published:       "badge-green",
  failed:          "badge-red",
  rejected:        "badge-red",
};

export default function ContentPage() {
  const qc = useQueryClient();
  const [generating, setGenerating] = useState(false);
  const [form, setForm] = useState({
    platform: "facebook",
    content_type: "image_post",
    topic: "educational",
    target_audience: "solar installers",
    auto_generate_image: true,
  });
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [filter, setFilter] = useState<string>("");

  const { data: items, isLoading } = useQuery({
    queryKey: ["content-list", filter],
    queryFn: () => contentApi.list(filter ? { status: filter } : {}).then(r => r.data),
    refetchInterval: 15_000,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, approved, notes }: any) => contentApi.approve(id, { approved, notes }),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["content-list"] });
      toast.success(vars.approved ? "Content approved ✓" : "Content rejected");
      setSelectedItem(null);
    },
  });

  const publishMutation = useMutation({
    mutationFn: (id: string) => socialApi.publishNow(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["content-list"] });
      toast.success("Published successfully! 🚀");
    },
    onError: () => toast.error("Publish failed — check API connections"),
  });

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await contentApi.generate(form);
      qc.invalidateQueries({ queryKey: ["content-list"] });
      toast.success(`Content generated (${(res.data.confidence_score * 100).toFixed(0)}% confidence)`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-sed-dark">Content Generation</h1>
          <p className="text-sed-grey-mid text-sm mt-1">AI-generated, brand-verified content queue</p>
        </div>
      </div>

      {/* Generator Panel */}
      <div className="card border-sed-orange/20">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 bg-sed-orange rounded-lg flex items-center justify-center">
            <Zap size={15} className="text-white" />
          </div>
          <h2 className="font-semibold text-sed-dark">Generate New Content</h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="label">Platform</label>
            <select className="input" value={form.platform} onChange={e => setForm(f => ({ ...f, platform: e.target.value }))}>
              {PLATFORMS.map(p => <option key={p} value={p} className="capitalize">{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Content Type</label>
            <select className="input" value={form.content_type} onChange={e => setForm(f => ({ ...f, content_type: e.target.value }))}>
              {CONTENT_TYPES.map(t => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Topic</label>
            <select className="input" value={form.topic} onChange={e => setForm(f => ({ ...f, topic: e.target.value }))}>
              {TOPICS.map(t => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Target Audience</label>
            <select className="input" value={form.target_audience} onChange={e => setForm(f => ({ ...f, target_audience: e.target.value }))}>
              {AUDIENCES.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-sed-grey-mid cursor-pointer">
            <input type="checkbox" checked={form.auto_generate_image}
              onChange={e => setForm(f => ({ ...f, auto_generate_image: e.target.checked }))}
              className="rounded accent-sed-orange" />
            Auto-generate image
          </label>
          <button className="btn-primary flex items-center gap-2" onClick={handleGenerate} disabled={generating}>
            {generating ? <RefreshCw size={15} className="animate-spin" /> : <Zap size={15} />}
            {generating ? "Generating..." : "Generate Content"}
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2 flex-wrap">
        {["", "pending_review", "approved", "scheduled", "published"].map(s => (
          <button key={s}
            onClick={() => setFilter(s)}
            className={clsx(
              "px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
              filter === s ? "bg-sed-orange text-white" : "bg-white text-sed-grey-mid hover:text-sed-grey border border-gray-200"
            )}>
            {s === "" ? "All" : s.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Content List */}
      <div className="space-y-3">
        {isLoading && Array(4).fill(0).map((_, i) => <div key={i} className="skeleton h-20 rounded-2xl" />)}
        {items?.map((item: any) => (
          <div key={item.id}
            className="card hover:shadow-card-hover transition-shadow cursor-pointer"
            onClick={() => setSelectedItem(item)}>
            <div className="flex items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-sm font-semibold text-sed-dark truncate">{item.title}</span>
                  <span className={clsx("badge", STATUS_BADGE[item.status] || "badge-gray")}>{item.status}</span>
                  <span className="badge badge-gray capitalize">{item.platform}</span>
                  <span className="badge badge-gray">{item.content_type}</span>
                </div>
                <p className="text-sm text-sed-grey-mid line-clamp-2">{item.body}</p>
                {item.hashtags?.length > 0 && (
                  <p className="text-xs text-sed-orange mt-1 truncate">
                    {item.hashtags.slice(0, 5).map((h: string) => `#${h}`).join(" ")}
                  </p>
                )}
              </div>
              {item.image_url && (
                <img src={item.image_url} alt="" className="w-16 h-16 rounded-xl object-cover flex-shrink-0" />
              )}
              <div className="flex flex-col items-end gap-2">
                {item.confidence_score && (
                  <span className={clsx(
                    "text-xs font-bold px-2 py-1 rounded-lg",
                    item.confidence_score >= 0.85 ? "bg-green-100 text-green-700" :
                    item.confidence_score >= 0.7 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"
                  )}>
                    {(item.confidence_score * 100).toFixed(0)}%
                  </span>
                )}
                <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                  {item.status === "pending_review" && (
                    <>
                      <button className="p-1.5 bg-green-50 hover:bg-green-100 rounded-lg text-green-600 transition-colors"
                        onClick={() => approveMutation.mutate({ id: item.id, approved: true })}>
                        <Check size={14} />
                      </button>
                      <button className="p-1.5 bg-red-50 hover:bg-red-100 rounded-lg text-red-500 transition-colors"
                        onClick={() => approveMutation.mutate({ id: item.id, approved: false })}>
                        <X size={14} />
                      </button>
                    </>
                  )}
                  {item.status === "approved" && (
                    <button className="p-1.5 bg-blue-50 hover:bg-blue-100 rounded-lg text-blue-600 transition-colors"
                      onClick={() => publishMutation.mutate(item.id)}>
                      <Send size={14} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        {items?.length === 0 && (
          <div className="text-center py-16 text-sed-grey-mid">
            <FileText size={40} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No content found. Generate some above.</p>
          </div>
        )}
      </div>

      {/* Content Detail Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedItem(null)}>
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-bold text-sed-dark">{selectedItem.title}</h3>
              <button onClick={() => setSelectedItem(null)} className="p-2 hover:bg-gray-100 rounded-xl">
                <X size={16} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              {selectedItem.image_url && (
                <img src={selectedItem.image_url} alt="" className="w-full h-48 object-cover rounded-2xl" />
              )}
              <div>
                <p className="label">Content</p>
                <p className="text-sm text-sed-grey whitespace-pre-wrap bg-gray-50 rounded-xl p-4">{selectedItem.body}</p>
              </div>
              {selectedItem.hashtags?.length > 0 && (
                <div>
                  <p className="label">Hashtags</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedItem.hashtags.map((h: string) => (
                      <span key={h} className="badge badge-orange">#{h}</span>
                    ))}
                  </div>
                </div>
              )}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-sed-grey-mid">Platform</p>
                  <p className="text-sm font-medium capitalize">{selectedItem.platform}</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-sed-grey-mid">Status</p>
                  <p className="text-sm font-medium capitalize">{selectedItem.status}</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-sed-grey-mid">AI Confidence</p>
                  <p className="text-sm font-bold text-sed-orange">
                    {selectedItem.confidence_score ? `${(selectedItem.confidence_score * 100).toFixed(0)}%` : "—"}
                  </p>
                </div>
              </div>
              {selectedItem.status === "pending_review" && (
                <div className="flex gap-3 pt-2">
                  <button className="btn-primary flex-1 flex items-center justify-center gap-2"
                    onClick={() => approveMutation.mutate({ id: selectedItem.id, approved: true })}>
                    <Check size={15} /> Approve
                  </button>
                  <button className="btn-secondary flex-1 flex items-center justify-center gap-2"
                    onClick={() => approveMutation.mutate({ id: selectedItem.id, approved: false })}>
                    <X size={15} /> Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FileText(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14,2 14,8 20,8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10,9 9,9 8,9" />
    </svg>
  );
}
