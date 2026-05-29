"use client";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi, socialApi, stockApi } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  TrendingUp, Clock, CheckCircle,
  Package, Zap, Globe, MessageSquare, Linkedin,
  Facebook, Instagram, AlertCircle, RefreshCw, ArrowUpRight
} from "lucide-react";
import toast from "react-hot-toast";

const PLATFORM_META: Record<string, { Icon: any; color: string; bg: string }> = {
  facebook:  { Icon: Facebook,      color: "#3B82F6", bg: "#EFF6FF" },
  instagram: { Icon: Instagram,     color: "#EC4899", bg: "#FDF2F8" },
  linkedin:  { Icon: Linkedin,      color: "#2563EB", bg: "#EFF6FF" },
  whatsapp:  { Icon: MessageSquare, color: "#16A34A", bg: "#F0FDF4" },
};

function StatCard({ label, value, icon: Icon, iconColor, iconBg, change, changeDir }: any) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change && (
            <p className={`text-xs mt-1 font-medium flex items-center gap-1 ${changeDir === "up" ? "text-green-600" : "text-red-600"}`}>
              <ArrowUpRight size={11} />
              {change}
            </p>
          )}
        </div>
        <div className="p-2.5 rounded-lg flex-shrink-0" style={{ backgroundColor: iconBg }}>
          <Icon size={18} style={{ color: iconColor }} />
        </div>
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-white rounded-lg px-3 py-2 text-sm border border-gray-200 shadow-sm">
        <p className="text-gray-500 text-xs mb-1">{label}</p>
        <p className="text-gray-900 font-semibold">{payload[0].value} posts</p>
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
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Marketing Intelligence</h1>
          <p className="text-gray-500 text-sm mt-0.5">SED Energy · Live Overview</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            All Systems Active
          </div>
          <button
            onClick={() => toast.success("Dashboard refreshed")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 border border-gray-200 transition-all"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* Approval alert */}
      {pending && pending.length > 0 && (
        <div className="flex items-center justify-between px-5 py-3.5 rounded-xl bg-orange-50 border border-orange-200">
          <div className="flex items-center gap-3">
            <AlertCircle size={16} style={{ color: "#E8612A" }} />
            <span className="text-sm text-gray-700">
              <span className="font-bold" style={{ color: "#E8612A" }}>{pending.length}</span> content items awaiting your approval
            </span>
          </div>
          <a href="/social?tab=approval" className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: "#E8612A" }}>
            Review Now
          </a>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Published"  value={overview?.total_published ?? "—"}  icon={CheckCircle} iconColor="#16A34A" iconBg="#F0FDF4"  change={`${overview?.published_this_week ?? 0} this week`} changeDir="up" />
        <StatCard label="Pending Approval" value={overview?.pending_approval ?? "—"} icon={Clock}        iconColor="#D97706" iconBg="#FFFBEB" />
        <StatCard label="Total Reach"      value={overview?.total_reach ? overview.total_reach.toLocaleString() : "—"} icon={TrendingUp} iconColor="#E8612A" iconBg="#FFF7ED" />
        <StatCard label="AI Confidence"    value={overview?.avg_ai_confidence ? `${(overview.avg_ai_confidence * 100).toFixed(0)}%` : "—"} icon={Zap} iconColor="#7C3AED" iconBg="#F5F3FF" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold text-gray-900">Posts by Platform</h3>
            <span className="text-xs text-gray-400">All time</span>
          </div>
          {platformData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={platformData} barSize={28}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(0,0,0,0.04)" }} />
                <Bar dataKey="posts" fill="#E8612A" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-44 flex items-center justify-center text-gray-300 text-sm">No data yet</div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Platform Summary</h3>
          <div className="space-y-2">
            {stats?.published_by_platform
              ? Object.entries(stats.published_by_platform).map(([platform, count]) => {
                  const meta = PLATFORM_META[platform] || { Icon: Globe, color: "#6B7280", bg: "#F3F4F6" };
                  return (
                    <div key={platform} className="flex items-center justify-between px-3 py-2.5 rounded-lg border border-gray-100 bg-gray-50">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: meta.bg }}>
                          <meta.Icon size={14} style={{ color: meta.color }} />
                        </div>
                        <span className="text-sm font-medium text-gray-700 capitalize">{platform}</span>
                      </div>
                      <span className="text-sm font-bold text-gray-900">{count as number}</span>
                    </div>
                  );
                })
              : ["facebook", "instagram", "linkedin", "whatsapp"].map(p => (
                  <div key={p} className="skeleton h-11 rounded-lg" />
                ))
            }
          </div>
        </div>
      </div>

      {/* Pending + Stock */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Pending Review</h3>
            <a href="/social?tab=approval" className="text-xs font-medium" style={{ color: "#E8612A" }}>View all</a>
          </div>
          <div className="space-y-2">
            {pending?.slice(0, 4).map((item: any) => {
              const meta = PLATFORM_META[item.platform];
              const score = item.confidence_score ?? 0;
              return (
                <div key={item.id} className="flex items-start gap-3 px-3 py-2.5 rounded-lg border border-gray-100 bg-gray-50">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: meta?.bg || "#F3F4F6" }}>
                    {meta ? <meta.Icon size={13} style={{ color: meta.color }} /> : <Globe size={13} className="text-gray-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-800 truncate">{item.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5 capitalize">{item.platform} · {item.content_type}</p>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${score >= 0.85 ? "bg-green-50 text-green-700" : "bg-yellow-50 text-yellow-700"}`}>
                    {score ? `${(score * 100).toFixed(0)}%` : "—"}
                  </span>
                </div>
              );
            })}
            {(!pending || pending.length === 0) && (
              <p className="text-sm text-gray-400 text-center py-8">No content pending review</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Stock Alerts</h3>
            <a href="/stock" className="text-xs font-medium" style={{ color: "#E8612A" }}>View all</a>
          </div>
          <div className="space-y-2">
            {stockAlerts?.slice(0, 4).map((alert: any) => {
              const isNew = alert.alert_type === "new_arrival";
              const isLow = alert.alert_type === "low_stock";
              const iconColor = isNew ? "#E8612A" : isLow ? "#D97706" : "#DC2626";
              const iconBg   = isNew ? "#FFF7ED" : isLow ? "#FFFBEB" : "#FEF2F2";
              return (
                <div key={alert.id} className="flex items-center justify-between px-3 py-2.5 rounded-lg border border-gray-100 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: iconBg }}>
                      <Package size={13} style={{ color: iconColor }} />
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-700 capitalize">{alert.alert_type.replace("_", " ")}</p>
                      <p className="text-xs text-gray-400">{alert.new_qty} units</p>
                    </div>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${alert.content_triggered ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {alert.content_triggered ? "Sent" : "Pending"}
                  </span>
                </div>
              );
            })}
            {(!stockAlerts || stockAlerts.length === 0) && (
              <p className="text-sm text-gray-400 text-center py-8">No stock alerts</p>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
