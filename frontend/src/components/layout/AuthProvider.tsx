"use client";

import { useEffect, ReactNode } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useRouter, usePathname } from "next/navigation";

const publicPaths = ["/", "/auth"];

export default function AuthProvider({ children }: { children: ReactNode }) {
  const { loadFromStorage, isLoading, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (!isLoading && !user && !publicPaths.includes(pathname)) {
      router.push("/auth");
    }
  }, [isLoading, user, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a1a]">
        <div className="w-8 h-8 border-2 border-[#6366f1] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}
