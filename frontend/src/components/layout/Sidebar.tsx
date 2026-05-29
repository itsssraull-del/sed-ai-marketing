"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, FileText, Calendar, MessageSquare,
  BarChart3, Database, Image, Package, Settings,
  LogOut, Zap
} from "lucide-react";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { href: "/dashboard",  label: "Overview",          icon: LayoutDashboard },
  { href: "/content",    label: "Content Queue",     icon: FileText },
  { href: "/social",     label: "Social Scheduler",  icon: Calendar },
  { href: "/whatsapp",   label: "WhatsApp Manager",  icon: MessageSquare },
  { href: "/analytics",  label: "Analytics",         icon: BarChart3 },
  { href: "/knowledge",  label: "Knowledge Base",    icon: Database },
  { href: "/media",      label: "Media Studio",      icon: Image },
  { href: "/stock",      label: "Stock Monitor",     icon: Package },
  { href: "/settings",   label: "Settings",          icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 flex flex-col z-50"
      style={{ background: "#111111", borderRight: "1px solid #222222" }}>

      {/* Logo */}
      <div className="px-6 py-5 border-b border-[#222]">
        <div className="flex items-center gap-3">
          {/* SED Energy logo mark */}
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: "linear-gradient(135deg, #F26522, #D4521A)" }}>
            <Zap size={17} className="text-white" fill="white" />
          </div>
          <div className="leading-none">
            <div className="flex items-baseline gap-[3px]">
              <span className="text-[15px] font-black tracking-tight" style={{ color: "#F26522" }}>SED</span>
              <span className="text-[15px] font-black tracking-tight text-white/80"> ENERGY</span>
            </div>
            <p className="text-[10px] text-white/30 mt-0.5 font-medium tracking-widest uppercase">AI Marketing</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group",
                isActive
                  ? "text-white"
                  : "text-white/40 hover:text-white/80 hover:bg-white/5"
              )}
              style={isActive ? {
                background: "rgba(242,101,34,0.12)",
                border: "1px solid rgba(242,101,34,0.2)",
                color: "#F26522"
              } : {}}
            >
              <Icon
                size={16}
                className={clsx("flex-shrink-0 transition-colors", isActive ? "" : "group-hover:text-white/60")}
                style={isActive ? { color: "#F26522" } : {}}
              />
              <span>{label}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#F26522]" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* AI Status */}
      <div className="px-3 pb-3">
        <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
          style={{ background: "rgba(34,197,94,0.07)", border: "1px solid rgba(34,197,94,0.15)" }}>
          <div className="relative flex-shrink-0">
            <div className="w-2 h-2 bg-green-400 rounded-full" />
            <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping opacity-40" />
          </div>
          <span className="text-green-400 text-xs font-medium">AI System Active</span>
        </div>
      </div>

      {/* Sign out */}
      <div className="px-3 pb-4 border-t border-[#222] pt-3">
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/30 hover:text-white/60 hover:bg-white/5 transition-all text-sm">
          <LogOut size={15} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
