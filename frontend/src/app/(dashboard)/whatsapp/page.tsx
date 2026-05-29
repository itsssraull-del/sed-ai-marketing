"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { whatsappApi } from "@/lib/api";
import { MessageSquare, Send, Users, Zap } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const GROUP_TYPE_COLORS: Record<string,string> = {
  installer: "badge-orange", vip_client: "badge-blue", internal_sales: "badge-gray",
  epc: "badge-green", regional_installer: "badge-yellow", supplier: "badge-gray",
};

const TOPICS = ["stock_arrival","back_in_stock","low_stock_alert","educational_tip","price_opportunity","general_update","industry_news"];

export default function WhatsAppPage() {
  const qc = useQueryClient();
  const [selectedGroup, setSelectedGroup] = useState<any>(null);
  const [topic, setTopic] = useState("stock_arrival");
  const [generatedMessage, setGeneratedMessage] = useState("");
  const [generating, setGenerating] = useState(false);

  const { data: groups } = useQuery({ queryKey: ["wa-groups"], queryFn: () => whatsappApi.getGroups().then(r => r.data) });

  const handleGenerate = async () => {
    if (!selectedGroup) return toast.error("Select a group first");
    setGenerating(true);
    try {
      const r = await whatsappApi.generateMessage({ group_id: selectedGroup.group_id, topic });
      setGeneratedMessage(r.data.message);
      toast.success(`Message generated (${(r.data.confidence_score*100).toFixed(0)}% confidence)`);
    } catch { toast.error("Generation failed"); }
    finally { setGenerating(false); }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-sed-dark">WhatsApp Manager</h1>
        <p className="text-sed-grey-mid text-sm mt-1">AI-tailored messaging per group type and audience</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-3">
          <h3 className="font-semibold text-sed-dark">Groups ({groups?.length || 0})</h3>
          {groups?.map((g: any) => (
            <div key={g.id} onClick={() => setSelectedGroup(g)}
              className={clsx("card cursor-pointer transition-all", selectedGroup?.id === g.id ? "border-sed-orange shadow-sed" : "hover:shadow-card-hover")}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">{g.group_name}</span>
                <span className={clsx("badge", GROUP_TYPE_COLORS[g.group_type] || "badge-gray")}>{g.group_type.replace(/_/g," ")}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-sed-grey-mid">
                <span className="flex items-center gap-1"><Users size={11}/>{g.member_count} members</span>
                <span>{g.total_messages_sent} sent</span>
              </div>
            </div>
          ))}
          {(!groups || groups.length === 0) && <p className="text-sm text-sed-grey-mid text-center py-6">No groups configured</p>}
        </div>
        <div className="lg:col-span-2 card h-fit">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
              <MessageSquare size={15} className="text-white" />
            </div>
            <h3 className="font-semibold text-sed-dark">Generate Message</h3>
          </div>
          {selectedGroup ? (
            <div className="bg-orange-50 rounded-xl p-3 mb-4 text-sm text-sed-dark">
              Generating for: <span className="font-bold">{selectedGroup.group_name}</span>
              <span className={clsx("badge ml-2", GROUP_TYPE_COLORS[selectedGroup.group_type] || "badge-gray")}>{selectedGroup.group_type.replace(/_/g," ")}</span>
            </div>
          ) : (
            <p className="text-sm text-sed-grey-mid mb-4">← Select a group to generate a message</p>
          )}
          <div className="mb-4">
            <label className="label">Message Topic</label>
            <select className="input" value={topic} onChange={e => setTopic(e.target.value)}>
              {TOPICS.map(t => <option key={t} value={t}>{t.replace(/_/g," ")}</option>)}
            </select>
          </div>
          <button className="btn-primary w-full flex items-center justify-center gap-2 mb-5" onClick={handleGenerate} disabled={generating || !selectedGroup}>
            <Zap size={15} className={generating ? "animate-spin" : ""} />
            {generating ? "Generating..." : "Generate Message"}
          </button>
          {generatedMessage && (
            <div>
              <label className="label">Generated Message</label>
              <textarea
                className="input min-h-48 font-mono text-xs whitespace-pre-wrap"
                value={generatedMessage}
                onChange={e => setGeneratedMessage(e.target.value)}
              />
              <div className="flex gap-2 mt-3">
                <button className="btn-primary flex-1 flex items-center justify-center gap-2">
                  <Send size={14} /> Send to Group
                </button>
                <button className="btn-secondary" onClick={() => { navigator.clipboard.writeText(generatedMessage); toast.success("Copied!"); }}>
                  Copy
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
