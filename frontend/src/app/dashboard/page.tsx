"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Plus, Moon, Image, Video, Calendar } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI } from "@/lib/api";

interface Dream {
  id: string;
  title?: string;
  content: string;
  mood?: string;
  tags: string[];
  created_at: string;
  generations: any[];
}

export default function DashboardPage() {
  const { user, token } = useAuthStore();
  const [dreams, setDreams] = useState<Dream[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      loadDreams();
    }
  }, [token]);

  const loadDreams = async () => {
    try {
      const result: any = await dreamsAPI.list(token!, 1, 5);
      setDreams(result.dreams);
    } catch (err) {
      console.error("Failed to load dreams:", err);
    } finally {
      setLoading(false);
    }
  };

  const moodEmoji: Record<string, string> = {
    fantasy: "✨",
    peaceful: "🌙",
    scary: "👻",
    sad: "🌧️",
    exciting: "⚡",
    romantic: "💫",
    mysterious: "🔮",
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <h1 className="text-3xl font-bold text-white mb-2">
          Good evening, {user?.nickname || "Dreamer"} 🌙
        </h1>
        <p className="text-[#94a3b8]">What did you dream about? Record it and let AI bring it to life.</p>
      </motion.div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <Link
          href="/record"
          className="glass-card p-6 hover:border-[#6366f1]/40 transition-all group cursor-pointer"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#a855f7] flex items-center justify-center group-hover:scale-110 transition-transform">
              <Plus className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-white">Record a Dream</h3>
              <p className="text-sm text-[#94a3b8]">Describe your dream</p>
            </div>
          </div>
        </Link>

        <Link
          href="/gallery"
          className="glass-card p-6 hover:border-[#a855f7]/40 transition-all group cursor-pointer"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#a855f7] to-[#ec4899] flex items-center justify-center group-hover:scale-110 transition-transform">
              <Image className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-white">Dream Gallery</h3>
              <p className="text-sm text-[#94a3b8]">Browse AI creations</p>
            </div>
          </div>
        </Link>

        <div className="glass-card p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#0ea5e9] to-[#6366f1] flex items-center justify-center">
              <Calendar className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-white">This Month</h3>
              <p className="text-sm text-[#94a3b8]">
                {dreams.length} dream{dreams.length !== 1 ? "s" : ""} recorded
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Dreams */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Recent Dreams</h2>
          <Link href="/dreams" className="text-sm text-[#818cf8] hover:text-[#a855f7]">
            View all →
          </Link>
        </div>

        {loading ? (
          <div className="grid gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card p-6 animate-pulse">
                <div className="h-4 bg-[#2a2a5e] rounded w-1/3 mb-3" />
                <div className="h-3 bg-[#2a2a5e] rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : dreams.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Moon className="w-12 h-12 text-[#6366f1] mx-auto mb-4 opacity-50" />
            <p className="text-[#94a3b8] mb-4">No dreams recorded yet</p>
            <Link href="/record" className="dream-button inline-flex items-center gap-2">
              <Plus className="w-4 h-4" /> Record Your First Dream
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {dreams.map((dream, index) => (
              <motion.div
                key={dream.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Link
                  href={`/dreams/${dream.id}`}
                  className="glass-card p-6 block hover:border-[#6366f1]/30 transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {dream.mood && (
                          <span>{moodEmoji[dream.mood] || "💭"}</span>
                        )}
                        <h3 className="font-semibold text-white">
                          {dream.title || "Untitled Dream"}
                        </h3>
                      </div>
                      <p className="text-[#94a3b8] text-sm line-clamp-2">
                        {dream.content}
                      </p>
                      <div className="flex items-center gap-3 mt-3">
                        <span className="text-xs text-[#64748b]">
                          {new Date(dream.created_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </span>
                        {dream.generations.length > 0 && (
                          <span className="flex items-center gap-1 text-xs text-[#818cf8]">
                            <Image className="w-3 h-3" />
                            {dream.generations.filter((g: any) => g.type === "image").length}
                            <Video className="w-3 h-3 ml-1" />
                            {dream.generations.filter((g: any) => g.type === "video").length}
                          </span>
                        )}
                      </div>
                    </div>
                    {dream.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 ml-4">
                        {dream.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 rounded-full text-xs bg-[#6366f1]/10 text-[#818cf8]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
