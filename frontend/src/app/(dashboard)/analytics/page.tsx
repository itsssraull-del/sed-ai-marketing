"use client";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, Award, BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  const { data: overview } = useQuery({ queryKey: ["analytics-overview"], queryFn: () => analyticsApi.getOverview().then(r => r.data) });
  const { data: platforms } = useQuery({ queryKey: ["platform-breakdown"], queryFn: () => analyticsApi.getPlatformBreakdown().then(r => r.data) });
  const { data: contentTypes } = useQuery({ queryKey: ["content-type-perf"], queryFn: () => analyticsApi.getContentTypePerf().then(r => r.data) });
  const { data: topContent } = useQuery({ queryKey: ["top-content"], queryFn: () => analyticsApi.getTopContent().then(r => r.data) });

  const platformChartData = platforms
    ? Object.entries(platforms).map(([name, data]: any) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        "Avg ER%": data.avg_engagement_rate,
        "Posts": data.post_count,
      }))
    : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-sed-dark">Analytics</h1>
        <p className="text-sed-grey-mid text-sm mt-1">Performance insights across all platforms</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Published", value: overview?.total_published ?? "—" },
          { label: "Published This Week", value: overview?.published_this_week ?? "—" },
          { label: "Total Reach", value: overview?.total_reach ? `${(overview.total_reach/1000).toFixed(1)}K` : "—" },
          { label: "Total Engagement", value: overview?.total_engagement ? `${(overview.total_engagement/1000).toFixed(1)}K` : "—" },
        ].map(s => (
          <div key={s.label} className="card">
            <p className="text-xs text-sed-grey-mid">{s.label}</p>
            <p className="text-2xl font-bold text-sed-dark mt-1">{s.value}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-sed-dark mb-4">Engagement Rate by Platform</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={platformChartData}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} unit="%" />
              <Tooltip contentStyle={{ borderRadius: "12px", border: "none" }} />
              <Bar dataKey="Avg ER%" fill="#E85A0C" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3 className="font-semibold text-sed-dark mb-4">Content Type Performance</h3>
          <div className="space-y-3">
            {contentTypes?.map((ct: any) => (
              <div key={ct.content_type} className="flex items-center gap-3">
                <span className="text-xs text-sed-grey-mid w-28 truncate capitalize">{ct.content_type.replace(/_/g, " ")}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div className="bg-sed-orange h-2 rounded-full" style={{ width: `${Math.min(ct.avg_engagement_rate * 20, 100)}%` }} />
                </div>
                <span className="text-xs font-bold text-sed-dark">{ct.avg_engagement_rate}%</span>
              </div>
            ))}
            {(!contentTypes || contentTypes.length === 0) && <p className="text-sm text-sed-grey-mid text-center py-4">No data yet</p>}
          </div>
        </div>
      </div>
      <div className="card">
        <h3 className="font-semibold text-sed-dark mb-4">Top Performing Content</h3>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-sed-grey-mid border-b border-gray-100">
            <th className="pb-3">Title</th><th className="pb-3">Platform</th><th className="pb-3">Reach</th><th className="pb-3">ER%</th>
          </tr></thead>
          <tbody className="divide-y divide-gray-50">
            {topContent?.map((item: any) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="py-3 font-medium max-w-xs truncate">{item.title}</td>
                <td className="py-3 capitalize text-sed-grey-mid">{item.platform}</td>
                <td className="py-3 text-sed-grey-mid">{item.engagement.reach.toLocaleString()}</td>
                <td className="py-3 font-bold text-sed-orange">{item.engagement.engagement_rate}%</td>
              </tr>
            ))}
          </tbody>
        </table>
        {(!topContent || topContent.length === 0) && <p className="text-center text-sed-grey-mid text-sm py-6">Publish content to see analytics</p>}
      </div>
    </div>
  );
}
