"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api";
import { Settings, Activity, RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const JOB_LABELS: Record<string,string> = {
  publish_posts: "Publish Scheduled Posts",
  check_stock: "Check Stock Updates",
  fetch_analytics: "Fetch Platform Analytics",
  monitor_news: "Monitor Industry News",
  weekly_calendar: "Generate Weekly Calendar",
  analytics_report: "Weekly Analytics Report",
};

export default function SettingsPage() {
  const { data: jobs } = useQuery({ queryKey: ["scheduler-jobs"], queryFn: () => settingsApi.getSchedulerJobs().then(r => r.data) });
  const { data: health } = useQuery({ queryKey: ["service-health"], queryFn: () => settingsApi.checkServiceHealth().then(r => r.data), retry: false });

  const triggerMutation = useMutation({
    mutationFn: (job: string) => settingsApi.triggerJob(job),
    onSuccess: (_, job) => toast.success(`${JOB_LABELS[job] || job} triggered`),
    onError: () => toast.error("Job trigger failed"),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-sed-dark">Settings</h1>
        <p className="text-sed-grey-mid text-sm mt-1">System configuration, scheduler, and service health</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-sed-dark mb-4 flex items-center gap-2"><Activity size={16}/> Scheduler Jobs</h3>
          <div className="space-y-2">
            {Object.entries(JOB_LABELS).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-gray-50">
                <span className="text-sm font-medium">{label}</span>
                <button className="btn-secondary text-xs py-1 px-3 flex items-center gap-1"
                  onClick={() => triggerMutation.mutate(key)}
                  disabled={triggerMutation.isPending}>
                  <RefreshCw size={11} /> Run Now
                </button>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3 className="font-semibold text-sed-dark mb-4">Service Health</h3>
          <div className="space-y-2">
            {health?.services ? Object.entries(health.services).map(([service, data]: any) => (
              <div key={service} className="flex items-center justify-between p-3 rounded-xl bg-gray-50">
                <span className="text-sm font-medium capitalize">{service.replace(/_/g," ")}</span>
                <div className="flex items-center gap-2">
                  {data.status === "ok"
                    ? <><CheckCircle size={15} className="text-green-500"/><span className="text-xs text-green-600">Online</span></>
                    : data.status === "not_configured"
                    ? <span className="text-xs text-sed-grey-mid">Not configured</span>
                    : <><XCircle size={15} className="text-red-500"/><span className="text-xs text-red-500">Error</span></>
                  }
                </div>
              </div>
            )) : (
              <div className="space-y-2">{Array(5).fill(0).map((_,i)=><div key={i} className="skeleton h-11 rounded-xl"/>)}</div>
            )}
          </div>
        </div>
      </div>
      <div className="card bg-sed-dark text-white">
        <h3 className="font-semibold mb-2">SED Energy AI System v1.0</h3>
        <p className="text-white/60 text-sm">Autonomous AI marketing operations for South Africa's Tier 1 solar distributor.</p>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          {[["10","AI Agents"],["4","Platforms"],["RAG","Knowledge Engine"],["Automated","Publishing"]].map(([v,l]) => (
            <div key={l}><p className="text-sed-orange font-bold text-lg">{v}</p><p className="text-white/50 text-xs">{l}</p></div>
          ))}
        </div>
      </div>
    </div>
  );
}
