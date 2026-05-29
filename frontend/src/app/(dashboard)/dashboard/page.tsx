"use client";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi, socialApi, stockApi } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  TrendingUp, FileText, Clock, CheckCircle,
  Package, Zap, Globe, MessageSquare, Linkedin,
  Facebook, Instagram, AlertCircle, RefreshCw, ArrowUpRight
} from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const PLATFORM_META: Record<string, { Icon: any; color: string; bg: string }> = {
  facebook:  { Icon: Facebook,      color: "#3B82F6", bg: "rgba(59,130,246,0.12)" },
  instagram: { Icon: Instagram,     color: "#EC4899", bg: "rgba(236,72,153,0.12)" },
  linkedin:  { Icon: Linkedin,      color: "#60A5FA", bg: "rgba(96,165,250,0.12)" },
  whatsapp:  { Icon: MessageSquare, color: "#22C55E", bg: "rgba(34,197,94,0.12)"  },
};

function StatCard({ label, value, icon: Icon, iconColor, iconBg, change, changeDir }: any) {
  return (
    <div className="rounded-2xl p-5 border border-[#222] flex flex-col gap-3"
      style={{ background: "#181818" }}>
      <div className="flex items-start justify-between">
        <p className="text-sm text-white/40 font-medium">{label}</p>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: iconBg }}>
          <Icon size={17} style={{ color: iconColor }} />
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        {change && (
          <p className={clsx("text-xs mt-1 font-medium flex items-center gap-1",
            changeDir === "up" ? "text-green-400" : "text-red-400")}>
            <ArrowUpRight size={11} />
            {change}
          </p>
        )}
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-xl px-3 py-2 text-sm border border-[#333]"
        style={{ background: "#1A1A1A" }}>
        <p className="text-white/50 text-xs mb-1">{label}</p>
        <p className="text-white font-semibold">{payload[0].value} posts</p>
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const { data: overview } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsApi.getOverview().then(r => r.data),
    refetchInterval: 60_000,
  });

  const { data: stats } = useQuery({
    queryKey: ["social-stats"],
    queryFn: () => socialApi.getStats().then(r => r.data),
  });

  const { data: pending } = useQuery({
    queryKey: ["pending-approval"],
    queryFn: () => socialApi.getPendingApproval().then(r => r.data),
  });

  const { data: stockAlerts } = useQuery({
    queryKey: ["stock-alerts"],
    queryFn: () => stockApi.getAlerts(false).then(r => r.data),
  });

  const platformData = stats?.published_by_platform
    ? Object.entries(stats.published_by_platform).map(([name, posts]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        posts,
      }))
    : [];

  return (
    <div className="space-y-7 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Marketing Intelligence</h1>
          <p className="text-white/35 text-sm mt-0.5">SED Energy · Live Overview</p>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.15)", color: "#4ade80" }}>
            <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            All Systems Active
          </div>
          <button
            onClick={() => toast.success("Dashboard refreshed")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white/40 hover:text-white/70 hover:bg-white/5 border border-[#2A2A2A] transition-all">
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* Approval alert */}
      {pending && pending.length > 0 && (
        <div className="flex items-center justify-between px-5 py-3.5 rounded-2xl"
          style={{ background: "rgba(242,101,34,0.08)", border: "1px solid rgba(242,101,34,0.2)" }}>
          <div className="flex items-center gap-3">
            <AlertCircle size={16} style={{ color: "#F26522" }} />
            <span className="text-sm text-white/70">
              <span className="font-bold" style={{ color: "#F26522" }}>{pending.length}</span> content items awaiting your approval
            </span>
          </div>
          <a href="/social?tab=approval"
            className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white transition-all"
            style={{ background: "#F26522" }}>
            Review Now
          </a>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Published"  value={overview?.total_published ?? "—"}  icon={CheckCircle} iconColor="#22C55E" iconBg="rgba(34,197,94,0.12)"   change={`${overview?.published_this_week ?? 0} this week`} changeDir="up" />
        <StatCard label="Pending Approval" value={overview?.pending_approval ?? "—"} icon={Clock}        iconColor="#F59E0B" iconBg="rgba(245,158,11,0.12)" />
        <StatCard label="Total Reach"      value={overview?.total_reach ? overview.total_reach.toLocaleString() : "—"} icon={TrendingUp} iconColor="#F26522" iconBg="rgba(242,101,34,0.12)" />
        <StatCard label="AI Confidence"    value={overview?.avg_ai_confidence ? `${(overview.avg_ai_confidence * 100).toFixed(0)}%` : "—"} icon={Zap} iconColor="#A78BFA" iconBg="rgba(167,139,250,0.12)" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Bar chart */}
        <div className="rounded-2xl p-5 border border-[#222]" style={{ background: "#181818" }}>
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold text-white">Posts by Platform</h3>
            <span className="text-xs text-white/30">All time</span>
          </div>
          {platformData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={platformData} barSize={28}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                <Bar dataKey="posts" fill="#F26522" radius={[6, 6, 0, 0]}
                  style={{ filter: "drop-shadow(0 0 8px rgba(242,101,34,0.3))" }} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-44 flex items-center justify-center text-white/20 text-sm">No data yet</div>
          )}
        </div>

        {/* Platform summary */}
        <div className="rounded-2xl p-5 border border-[#222]" style={{ background: "#181818" }}>
          <h3 className="text-sm font-semibold text-white mb-4">Platform Summary</h3>
          <div className="space-y-2">
            {stats?.published_by_platform
              ? Object.entries(stats.published_by_platform).map(([platform, count]) => {
                  const meta = PLATFORM_META[platform] || { Icon: Globe, color: "#888", bg: "rgba(255,255,255,0.07)" };
                  return (
                    <div key={platform} className="flex items-center justify-between px-3 py-2.5 rounded-xl transition-colors"
                      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid #222" }}>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ background: meta.bg }}>
                          <meta.Icon size={14} style={{ color: meta.color }} />
                        </div>
                        <span className="text-sm font-medium text-white/70 capitalize">{platform}</span>
                      </div>
                      <span className="text-sm font-bold text-white">{count as number}</span>
                    </div>
                  );
                })
              : ["facebook", "instagram", "linkedin", "whatsapp"].map(p => (
                  <div key={p} className="skeleton h-11 rounded-xl" />
                ))
            }
          </div>
        </div>
      </div>

      {/* Pending + Stock */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Pending review */}
        <div className="rounded-2xl p-5 border border-[#222]" style={{ background: "#181818" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Pending Review</h3>
            <a href="/social?tab=approval" className="text-xs font-medium transition-colors"
              style={{ color: "#F26522" }}>View all</a>
          </div>
          <div className="space-y-2">
            {pending?.slice(0, 4).map((item: any) => {
              const meta = PLATFORM_META[item.platform];
              const score = item.confidence_score ?? 0;
              return (
                <div key={item.id}
                  className="flex items-start gap-3 px-3 py-2.5 rounded-xl transition-colors group"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid #222" }}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: meta?.bg || "rgba(255,255,255,0.07)" }}>
                    {meta ? <meta.Icon size={13} style={{ color: meta.color }} /> : <Globe size={13} className="text-white/40" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white/80 truncate">{item.title}</p>
                    <p className="text-xs text-white/30 mt-0.5 capitalize">{item.platform} · {item.content_type}</p>
                  </div>
                  <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full",
                    score >= 0.85 ? "text-green-400" : "text-yellow-400")}
                    style={{ background: score >= 0.85 ? "rgba(34,197,94,0.1)" : "rgba(245,158,11,0.1)" }}>
                    {score ? `${(score * 100).toFixed(0)}%` : "—"}
                  </span>
                </div>
              );
            })}
            {(!pending || pending.length === 0) && (
              <p className="text-sm text-white/20 text-center py-8">No content pending review</p>
            )}
          </div>
        </div>

        {/* Stock alerts */}
        <div className="rounded-2xl p-5 border border-[#222]" style={{ background: "#181818" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Stock Alerts</h3>
            <a href="/stock" className="text-xs font-medium" style={{ color: "#F26522" }}>View all</a>
          </div>
          <div className="space-y-2">
            {stockAlerts?.slice(0, 4).map((alert: any) => {
              const isNew = alert.alert_type === "new_arrival";
              const isLow = alert.alert_type === "low_stock";
              const iconColor = isNew ? "#F26522" : isLow ? "#F59E0B" : "#EF4444";
              const iconBg = isNew ? "rgba(242,101,34,0.12)" : isLow ? "rgba(245,158,11,0.12)" : "rgba(239,68,68,0.12)";
              return (
                <div key={alert.id} className="flex items-center justify-between px-3 py-2.5 rounded-xl"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid #222" }}>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ background: iconBg }}>
                      <Package size={13} style={{ color: iconColor }} />
                    </div>
                    <div>
                      <p className="text-xs font-medium text-white/70 capitalize">{alert.alert_type.replace("_", " ")}</p>
                      <p className="text-xs text-white/30">{alert.new_qty} units</p>
                    </div>
                  </div>
                  <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full",
                    alert.content_triggered ? "text-green-400" : "text-white/30")}
                    style={{ background: alert.content_triggered ? "rgba(34,197,94,0.1)" : "rgba(255,255,255,0.05)" }}>
                    {alert.content_triggered ? "Sent" : "Pending"}
                  </span>
                </div>
              );
            })}
            {(!stockAlerts || stockAlerts.length === 0) && (
              <p className="text-sm text-white/20 text-center py-8">No stock alerts</p>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
