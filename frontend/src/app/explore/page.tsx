"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Compass, Play } from "lucide-react";
import { galleryAPI } from "@/lib/api";

interface GalleryItem {
  id: string;
  type: "image" | "video";
  result_url: string;
  dream_title: string;
  user: string;
  avatar_url: string | null;
  featured_at: string | null;
  created_at: string | null;
}

export default function ExplorePage() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    galleryAPI.list(1, 20)
      .then((res) => {
        setItems(res.items || []);
        setTotal(res.total || 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="main-content min-h-screen px-8 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Explore</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Today's top dream visualizations
            {total > 0 && <span className="ml-2 text-[var(--text-muted)]">({total} works)</span>}
          </p>
        </div>

        {loading ? (
          <div className="text-center py-24">
            <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-[var(--text-muted)]">Loading gallery...</p>
          </div>
        ) : items.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-24"
          >
            <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] flex items-center justify-center mx-auto mb-4">
              <Compass className="w-7 h-7 text-[var(--text-muted)]" />
            </div>
            <p className="text-[var(--text-secondary)] mb-2">No featured works yet</p>
            <p className="text-sm text-[var(--text-muted)]">
              The most beautiful dream visualizations will appear here once curated
            </p>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="gallery-grid"
          >
            {items.map((item, i) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="gallery-card group"
              >
                <div className="relative aspect-square rounded-xl overflow-hidden bg-[var(--bg-elevated)]">
                  {item.type === "image" ? (
                    <img
                      src={item.result_url}
                      alt={item.dream_title}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="relative w-full h-full">
                      <video
                        src={item.result_url}
                        className="w-full h-full object-cover"
                        muted
                        loop
                        playsInline
                        onMouseOver={(e) => (e.target as HTMLVideoElement).play()}
                        onMouseOut={(e) => { const v = e.target as HTMLVideoElement; v.pause(); v.currentTime = 0; }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-80 group-hover:opacity-0 transition-opacity">
                        <div className="w-10 h-10 rounded-full bg-black/50 flex items-center justify-center">
                          <Play className="w-4 h-4 text-white ml-0.5" />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Overlay on hover */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-0 left-0 right-0 p-3">
                      <p className="text-white text-sm font-medium truncate">{item.dream_title}</p>
                      <p className="text-white/70 text-xs mt-0.5">{item.user}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}
