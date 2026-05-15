"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Image as ImageIcon, Video, Clock, Plus } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI } from "@/lib/api";

interface Generation {
  id: string;
  type: "image" | "video";
  status: string;
  result_url?: string;
}

interface Dream {
  id: string;
  title?: string;
  content: string;
  tags: string[];
  created_at: string;
  generations: Generation[];
}

export default function DreamsPage() {
  const { token } = useAuthStore();
  const [dreams, setDreams] = useState<Dream[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) loadDreams();
  }, [token]);

  const loadDreams = async () => {
    try {
      const result: any = await dreamsAPI.list(token!, 1, 50);
      const list = result.dreams || result.items || result;
      setDreams(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error("Failed to load dreams:", err);
    } finally {
      setLoading(false);
    }
  };

  const getThumbnail = (dream: Dream): string | null => {
    const completedImage = dream.generations?.find(
      (g) => g.type === "image" && g.status === "completed" && g.result_url
    );
    return completedImage?.result_url || null;
  };

  if (loading) {
    return (
      <div className="main-content min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="main-content min-h-screen px-8 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">My Dreams</h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              {dreams.length} dreams recorded
            </p>
          </div>
          <Link href="/create" className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Dream
          </Link>
        </div>

        {/* Dreams Grid */}
        {dreams.length === 0 ? (
          <div className="text-center py-24">
            <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] flex items-center justify-center mx-auto mb-4">
              <ImageIcon className="w-7 h-7 text-[var(--text-muted)]" />
            </div>
            <p className="text-[var(--text-secondary)] mb-2">No dreams yet</p>
            <p className="text-sm text-[var(--text-muted)] mb-6">
              Record your first dream and watch AI bring it to life
            </p>
            <Link href="/create" className="btn-primary">
              Record a Dream
            </Link>
          </div>
        ) : (
          <div className="gallery-grid">
            {dreams.map((dream, i) => {
              const thumbnail = getThumbnail(dream);
              const imageCount = dream.generations?.filter(g => g.type === "image").length || 0;
              const videoCount = dream.generations?.filter(g => g.type === "video").length || 0;

              return (
                <motion.div
                  key={dream.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                >
                  <Link href={`/dreams/${dream.id}`} className="card block overflow-hidden group">
                    {/* Thumbnail */}
                    <div className="aspect-[4/3] relative overflow-hidden bg-[var(--bg-elevated)]">
                      {thumbnail ? (
                        <img
                          src={thumbnail}
                          alt={dream.title || "Dream"}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <ImageIcon className="w-8 h-8 text-[var(--text-muted)] opacity-30" />
                        </div>
                      )}

                      {/* Overlay badges */}
                      <div className="absolute bottom-2 right-2 flex gap-1.5">
                        {imageCount > 0 && (
                          <span className="px-2 py-0.5 rounded-md bg-black/60 text-[10px] text-white flex items-center gap-1">
                            <ImageIcon className="w-3 h-3" /> {imageCount}
                          </span>
                        )}
                        {videoCount > 0 && (
                          <span className="px-2 py-0.5 rounded-md bg-black/60 text-[10px] text-white flex items-center gap-1">
                            <Video className="w-3 h-3" /> {videoCount}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-4">
                      <h3 className="text-sm font-medium text-[var(--text-primary)] truncate">
                        {dream.title || "Untitled Dream"}
                      </h3>
                      <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-2">
                        {dream.content}
                      </p>
                      <div className="flex items-center gap-2 mt-3">
                        <Clock className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-xs text-[var(--text-muted)]">
                          {new Date(dream.created_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
