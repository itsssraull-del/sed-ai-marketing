"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { stockApi } from "@/lib/api";
import { Package, AlertTriangle, RefreshCw, Zap } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";

const STATUS_COLOR: Record<string,string> = {
  in_stock: "badge-green", low_stock: "badge-yellow",
  out_of_stock: "badge-red", arriving_soon: "badge-blue",
};

export default function StockPage() {
  const qc = useQueryClient();
  const [brand, setBrand] = useState("");
  const { data: items, isLoading } = useQuery({
    queryKey: ["stock", brand],
    queryFn: () => stockApi.list(brand ? { brand } : {}).then(r => r.data),
    refetchInterval: 30_000,
  });
  const { data: alerts } = useQuery({
    queryKey: ["stock-alerts-unprocessed"],
    queryFn: () => stockApi.getAlerts(false).then(r => r.data),
  });
  const syncMutation = useMutation({
    mutationFn: () => stockApi.sagSync(),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["stock"] }); toast.success("Sage sync triggered"); },
  });

  const BRANDS = ["Sungrow","Hinen","Astronergy","Hanersun","Sunova","Powerco","Grenex","Knyee","PROJOY"];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-sed-dark">Stock Monitor</h1>
          <p className="text-sed-grey-mid text-sm mt-1">Live inventory levels and automated content triggers</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
          <RefreshCw size={14} className={syncMutation.isPending ? "animate-spin" : ""} /> Sage Sync
        </button>
      </div>
      {alerts && alerts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-4 flex items-center gap-3">
          <AlertTriangle size={18} className="text-yellow-600" />
          <span className="text-sm font-medium">{alerts.length} unprocessed stock alert{alerts.length > 1 ? "s" : ""}</span>
        </div>
      )}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setBrand("")} className={clsx("px-3 py-1.5 rounded-full text-xs font-medium border transition-colors", brand === "" ? "bg-sed-orange text-white border-sed-orange" : "bg-white text-sed-grey-mid border-gray-200")}>All Brands</button>
        {BRANDS.map(b => <button key={b} onClick={() => setBrand(b)} className={clsx("px-3 py-1.5 rounded-full text-xs font-medium border transition-colors", brand === b ? "bg-sed-orange text-white border-sed-orange" : "bg-white text-sed-grey-mid border-gray-200")}>{b}</button>)}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading && Array(6).fill(0).map((_,i) => <div key={i} className="skeleton h-36 rounded-2xl"/>)}
        {items?.map((item: any) => (
          <div key={item.id} className="card hover:shadow-card-hover transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center">
                <Package size={18} className="text-sed-orange" />
              </div>
              <span className={clsx("badge", STATUS_COLOR[item.status] || "badge-gray")}>{item.status.replace(/_/g," ")}</span>
            </div>
            <h3 className="font-semibold text-sed-dark text-sm leading-tight">{item.name}</h3>
            <p className="text-xs text-sed-grey-mid mt-0.5">{item.brand} · {item.category.replace(/_/g," ")}</p>
            <div className="mt-3 flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-sed-dark">{item.quantity_on_hand}</p>
                <p className="text-xs text-sed-grey-mid">units on hand</p>
              </div>
              {item.is_featured && <span className="badge badge-orange">Featured</span>}
            </div>
            {item.quantity_on_hand <= item.low_stock_threshold && item.quantity_on_hand > 0 && (
              <div className="mt-2 flex items-center gap-1.5 text-yellow-600">
                <AlertTriangle size={12} /><span className="text-xs">Low stock warning</span>
              </div>
            )}
          </div>
        ))}
        {items?.length === 0 && <p className="col-span-3 text-center text-sed-grey-mid text-sm py-12">No stock items found</p>}
      </div>
    </div>
  );
}
