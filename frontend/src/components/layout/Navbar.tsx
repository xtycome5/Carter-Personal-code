"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";
import { Moon, LogOut, User, ImageIcon } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card rounded-none border-x-0 border-t-0">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2">
          <Moon className="w-6 h-6 text-[#a855f7]" />
          <span className="text-lg font-bold bg-gradient-to-r from-[#6366f1] to-[#a855f7] bg-clip-text text-transparent">
            Dream Recorder
          </span>
        </Link>

        {/* Nav Links */}
        {user && (
          <div className="hidden md:flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-[#94a3b8] hover:text-white transition-colors"
            >
              首页
            </Link>
            <Link
              href="/record"
              className="text-[#94a3b8] hover:text-white transition-colors"
            >
              记录梦境
            </Link>
            <Link
              href="/gallery"
              className="text-[#94a3b8] hover:text-white transition-colors"
            >
              梦境画廊
            </Link>
          </div>
        )}

        {/* User Menu */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-[#94a3b8]">
                <User className="w-4 h-4" />
                <span>{user.nickname || user.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-[#94a3b8] hover:text-white transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link href="/auth" className="dream-button text-sm py-2 px-4">
              开始记录
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
