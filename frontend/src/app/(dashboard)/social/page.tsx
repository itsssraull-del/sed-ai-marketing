"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { socialApi, contentApi } from "@/lib/api";
import { Calendar, Send, Check, X, Clock } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const STATUS_COLOR: Record<string,string> = {
  approved: "badge-green", scheduled: "badge-blue",
  pending_review: "badge-yellow", published: "badge-gray",
};

export default function SocialPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"calendar"|"approval"|"published">("calendar");

  const { data: calendar } = useQuery({ queryKey: ["calendar"], queryFn: () => socialApi.getCalendar().then(r => r.data), enabled: tab === "calendar" });
  const { data: pending } = useQuery({ queryKey: ["pending"], queryFn: () => socialApi.getPendingApproval().then(r => r.data), refetchInterval: 15_000, enabled: tab === "approval" });
  const { data: published } = useQuery({ queryKey: ["published"], queryFn: () => socialApi.getPublished().then(r => r.data), enabled: tab === "published" });

  const approveMutation = useMutation({
    mutationFn: ({ id, approved }: any) => contentApi.approve(id, { approved }),
    onSuccess: (_, { approved }) => { qc.invalidateQueries({ queryKey: ["pending"] }); toast.success(approved ? "Approved ✓" : "Rejected"); },
  });

  const publishMutation = useMutation({
    mutationFn: (id: string) => socialApi.publishNow(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["calendar","published"] }); toast.success("Published! 🚀"); },
    onError: () => toast.error("Publish failed"),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-sed-dark">Social Scheduler</h1>
        <p className="text-sed-grey-mid text-sm mt-1">Content calendar, approval queue, and publishing</p>
      </div>
      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl w-fit">
        {[["calendar","Calendar"],["approval","Approval Queue"],["published","Published"]].map(([t,l]) => (
          <button key={t} onClick={() => setTab(t as any)}
            className={clsx("px-4 py-2 rounded-lg text-sm font-medium transition-colors", tab === t ? "bg-white text-sed-dark shadow-sm" : "text-sed-grey-mid")}>
            {l}
          </button>
        ))}
      </div>
      {tab === "calendar" && (
        <div className="space-y-3">
          {calendar?.map((item: any) => (
            <div key={item.id} className="card flex items-center gap-4">
              {item.image_url && <img src={item.image_url} alt="" className="w-14 h-14 rounded-xl object-cover flex-shrink-0"/>}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="font-medium text-sm truncate">{item.title}</span>
                  <span className={clsx("badge", STATUS_COLOR[item.status] || "badge-gray")}>{item.status}</span>
                  <span className="badge badge-gray capitalize">{item.platform}</span>
                </div>
                {item.scheduled_for && (
                  <p className="text-xs text-sed-grey-mid flex items-center gap-1"><Clock size={11}/>{new Date(item.scheduled_for).toLocaleString()}</p>
                )}
              </div>
              {item.status === "approved" && (
                <button className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1" onClick={() => publishMutation.mutate(item.id)}>
                  <Send size={12}/> Publish
                </button>
              )}
            </div>
          ))}
          {(!calendar || calendar.length === 0) && <p className="text-center text-sed-grey-mid text-sm py-12">No scheduled content</p>}
        </div>
      )}
      {tab === "approval" && (
        <div className="space-y-3">
          {pending?.map((item: any) => (
            <div key={item.id} className="card">
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-sm">{item.title}</span>
                    <span className="badge badge-gray capitalize">{item.platform}</span>
                    {item.confidence_score && <span className={clsx("badge", item.confidence_score>=0.85?"badge-green":"badge-yellow")}>{(item.confidence_score*100).toFixed(0)}%</span>}
                  </div>
                  <p className="text-sm text-sed-grey line-clamp-3">{item.body}</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button className="p-2 bg-green-50 hover:bg-green-100 rounded-xl text-green-600" onClick={() => approveMutation.mutate({ id: item.id, approved: true })}><Check size={15}/></button>
                  <button className="p-2 bg-red-50 hover:bg-red-100 rounded-xl text-red-500" onClick={() => approveMutation.mutate({ id: item.id, approved: false })}><X size={15}/></button>
                </div>
              </div>
            </div>
          ))}
          {(!pending || pending.length === 0) && <p className="text-center text-sed-grey-mid text-sm py-12">Nothing pending — all clear!</p>}
        </div>
      )}
      {tab === "published" && (
        <div className="space-y-3">
          {published?.map((item: any) => (
            <div key={item.id} className="card flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm truncate">{item.title}</span>
                  <span className="badge badge-gray capitalize">{item.platform}</span>
                </div>
                <p className="text-xs text-sed-grey-mid">Published {item.published_at ? new Date(item.published_at).toLocaleDateString() : "—"}</p>
              </div>
              <div className="text-right text-xs text-sed-grey-mid flex gap-4">
                <div><p className="font-bold text-sed-dark text-base">{item.engagement.likes}</p><p>Likes</p></div>
                <div><p className="font-bold text-sed-dark text-base">{item.engagement.comments}</p><p>Comments</p></div>
                <div><p className="font-bold text-sed-dark text-base">{item.engagement.reach?.toLocaleString()}</p><p>Reach</p></div>
              </div>
            </div>
          ))}
          {(!published || published.length === 0) && <p className="text-center text-sed-grey-mid text-sm py-12">No published posts yet</p>}
        </div>
      )}
    </div>
  );
}
