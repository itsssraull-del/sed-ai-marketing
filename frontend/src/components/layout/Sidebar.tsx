"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, FileText, Calendar, MessageSquare,
  BarChart3, Database, Image, Package, Settings, LogOut,
} from "lucide-react";
import Cookies from "js-cookie";

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
  const router = useRouter();

  function handleSignOut() {
    Cookies.remove("access_token");
    router.push("/login");
  }

  return (
    <aside
      className="fixed left-0 top-0 h-screen w-64 flex flex-col z-50"
      style={{ backgroundColor: "#1C1C1C" }}
    >
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="flex items-baseline gap-0 leading-none">
          <span className="font-extrabold text-2xl tracking-tight" style={{ color: "#E8612A" }}>SED</span>
          <span className="font-light text-2xl tracking-widest text-white ml-1.5">ENERGY</span>
        </div>
        <div className="text-xs text-white/35 mt-1 tracking-widest uppercase font-medium">AI Marketing</div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={[
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "text-white"
                  : "text-white/60 hover:bg-white/[0.08] hover:text-white",
              ].join(" ")}
              style={isActive ? { backgroundColor: "#E8612A" } : undefined}
            >
              <Icon size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Sign out */}
      <div className="px-3 pb-4 pt-3 border-t border-white/10">
        <button
          onClick={handleSignOut}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-white/40 hover:bg-white/[0.08] hover:text-white transition-colors"
        >
          <LogOut size={15} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
