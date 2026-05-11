"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Image as ImageIcon, Video, Filter } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI } from "@/lib/api";

interface Generation {
  id: string;
  type: "image" | "video";
  style?: string;
  status: string;
  result_url?: string;
  created_at: string;
  dream_id: string;
}

interface Dream {
  id: string;
  title?: string;
  content: string;
  generations: Generation[];
  created_at: string;
}

export default function GalleryPage() {
  const { token } = useAuthStore();
  const [dreams, setDreams] = useState<Dream[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "image" | "video">("all");

  useEffect(() => {
    if (token) {
      loadDreams();
    }
  }, [token]);

  const loadDreams = async () => {
    try {
      const result: any = await dreamsAPI.list(token!, 1, 100);
      setDreams(result.dreams);
    } catch (err) {
      console.error("Failed to load gallery:", err);
    } finally {
      setLoading(false);
    }
  };

  // Flatten all completed generations
  const allGenerations = dreams.flatMap((dream) =>
    dream.generations
      .filter((g) => g.status === "completed" && g.result_url)
      .map((g) => ({ ...g, dreamTitle: dream.title, dreamContent: dream.content }))
  );

  const filteredGenerations = allGenerations.filter((g) =>
    filter === "all" ? true : g.type === filter
  );

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">梦境画廊</h1>
            <p className="text-[#94a3b8] mt-1">你的所有 AI 生成作品</p>
          </div>

          {/* Filter */}
          <div className="flex gap-2">
            {[
              { id: "all", label: "全部" },
              { id: "image", label: "图片", icon: ImageIcon },
              { id: "video", label: "视频", icon: Video },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id as any)}
                className={`px-4 py-2 rounded-lg text-sm transition-all flex items-center gap-1 ${
                  filter === f.id
                    ? "bg-[#6366f1]/20 border border-[#6366f1]/50 text-white"
                    : "border border-[#2a2a5e] text-[#94a3b8] hover:border-[#6366f1]/30"
                }`}
              >
                {f.icon && <f.icon className="w-3 h-3" />}
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Gallery Grid */}
        {loading ? (
          <div className="grid md:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="glass-card aspect-square animate-pulse bg-[#1a1a3e]" />
            ))}
          </div>
        ) : filteredGenerations.length === 0 ? (
          <div className="glass-card p-16 text-center">
            <ImageIcon className="w-16 h-16 text-[#6366f1] mx-auto mb-4 opacity-30" />
            <p className="text-[#94a3b8] mb-2">画廊还是空的</p>
            <p className="text-[#64748b] text-sm mb-6">
              记录梦境并生成图片/视频后，它们会出现在这里
            </p>
            <Link href="/record" className="dream-button inline-block">
              去记录梦境
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-4">
            {filteredGenerations.map((gen: any, index) => (
              <motion.div
                key={gen.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link
                  href={`/dreams/${gen.dream_id}`}
                  className="glass-card overflow-hidden block group hover:border-[#6366f1]/40 transition-all"
                >
                  {gen.type === "image" ? (
                    <img
                      src={gen.result_url}
                      alt={gen.dreamTitle || "Dream"}
                      className="w-full aspect-square object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <video
                      src={gen.result_url}
                      className="w-full aspect-video object-cover"
                      muted
                      onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                      onMouseLeave={(e) => {
                        const v = e.target as HTMLVideoElement;
                        v.pause();
                        v.currentTime = 0;
                      }}
                    />
                  )}
                  <div className="p-3">
                    <p className="text-sm text-white truncate">
                      {gen.dreamTitle || gen.dreamContent?.slice(0, 30)}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {gen.type === "image" ? (
                        <ImageIcon className="w-3 h-3 text-[#6366f1]" />
                      ) : (
                        <Video className="w-3 h-3 text-[#a855f7]" />
                      )}
                      <span className="text-xs text-[#64748b]">
                        {gen.style} · {new Date(gen.created_at).toLocaleDateString("zh-CN")}
                      </span>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
