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
    // If logged in and on landing or auth page, redirect to create
    if (!isLoading && user && (pathname === "/" || pathname === "/auth")) {
      router.push("/create");
    }
  }, [isLoading, user, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#7c5cfc] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}
