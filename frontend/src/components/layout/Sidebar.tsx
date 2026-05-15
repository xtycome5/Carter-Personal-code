"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import {
  Compass,
  PenLine,
  FolderOpen,
  Star,
  LogOut,
  Moon,
} from "lucide-react";

const navItems = [
  { href: "/create", icon: PenLine, label: "Create" },
  { href: "/explore", icon: Compass, label: "Explore" },
  { href: "/dreams", icon: FolderOpen, label: "My Dreams" },
  { href: "/favorites", icon: Star, label: "Favorites" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  if (!user) return null;

  return (
    <aside className="sidebar">
      {/* Logo */}
      <Link href="/create" className="mb-6 mt-1">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7c5cfc] to-[#c084fc] flex items-center justify-center">
          <Moon className="w-5 h-5 text-white" />
        </div>
      </Link>

      {/* Navigation */}
      <nav className="flex flex-col items-center gap-1 flex-1">
        {navItems.map(({ href, icon: Icon, label }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href} className="relative group">
              <div className={`sidebar-item ${isActive ? "active" : ""}`}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="sidebar-tooltip">{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="flex flex-col items-center gap-2 mt-auto">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#6366f1] to-[#a855f7] flex items-center justify-center text-xs font-bold text-white">
          {user.nickname?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
        </div>
        <button
          onClick={logout}
          className="sidebar-item !w-9 !h-9"
          title="Log out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
