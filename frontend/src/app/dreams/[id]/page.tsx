"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Image as ImageIcon, Video, Wand2, RefreshCw, Download } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI, generateAPI } from "@/lib/api";

interface Generation {
  id: string;
  type: "image" | "video";
  style?: string;
  status: string;
  result_url?: string;
  created_at: string;
}

interface Dream {
  id: string;
  title?: string;
  content: string;
  enhanced_content?: string;
  mood?: string;
  tags: string[];
  created_at: string;
  generations: Generation[];
}

export default function DreamDetailPage() {
  const params = useParams();
  const dreamId = params.id as string;
  const { token } = useAuthStore();

  const [dream, setDream] = useState<Dream | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [polling, setPolling] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (token && dreamId) {
      loadDream();
    }
  }, [token, dreamId]);

  // Poll for generation status
  useEffect(() => {
    if (polling.size === 0) return;

    const interval = setInterval(async () => {
      for (const genId of polling) {
        try {
          const result: any = await generateAPI.checkStatus(token!, genId);
          if (result.status === "completed" || result.status === "failed") {
            setPolling((prev) => {
              const next = new Set(prev);
              next.delete(genId);
              return next;
            });
            loadDream(); // Refresh dream data
          }
        } catch (err) {
          console.error("Poll error:", err);
        }
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [polling, token]);

  const loadDream = async () => {
    try {
      const result: any = await dreamsAPI.get(token!, dreamId);
      setDream(result);
      // Check for processing generations
      const processingIds = result.generations
        .filter((g: Generation) => g.status === "processing")
        .map((g: Generation) => g.id);
      if (processingIds.length > 0) {
        setPolling(new Set(processingIds));
      }
    } catch (err) {
      console.error("Failed to load dream:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateImage = async (style: string) => {
    if (!dream) return;
    setGenerating("image");
    try {
      // Enhance first if not already enhanced
      if (!dream.enhanced_content) {
        await generateAPI.enhance(token!, { dream_id: dream.id, style });
      }
      const gen: any = await generateAPI.image(token!, {
        dream_id: dream.id,
        style,
      });
      setPolling((prev) => new Set(prev).add(gen.id));
      loadDream();
    } catch (err: any) {
      alert(err.message || "生成失败");
    } finally {
      setGenerating(null);
    }
  };

  const handleGenerateVideo = async (style: string) => {
    if (!dream) return;
    setGenerating("video");
    try {
      if (!dream.enhanced_content) {
        await generateAPI.enhance(token!, { dream_id: dream.id, style });
      }
      const gen: any = await generateAPI.video(token!, {
        dream_id: dream.id,
        style,
        duration: 5,
        resolution: "720P",
      });
      setPolling((prev) => new Set(prev).add(gen.id));
      loadDream();
    } catch (err: any) {
      alert(err.message || "生成失败");
    } finally {
      setGenerating(null);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="glass-card p-8 animate-pulse">
          <div className="h-6 bg-[#2a2a5e] rounded w-1/3 mb-4" />
          <div className="h-4 bg-[#2a2a5e] rounded w-2/3 mb-2" />
          <div className="h-4 bg-[#2a2a5e] rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (!dream) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 text-center text-[#94a3b8]">
        梦境不存在
      </div>
    );
  }

  const images = dream.generations.filter((g) => g.type === "image");
  const videos = dream.generations.filter((g) => g.type === "video");

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        {/* Dream Content */}
        <div className="glass-card p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h1 className="text-2xl font-bold text-white">
              {dream.title || "未命名的梦"}
            </h1>
            {dream.mood && (
              <span className="px-3 py-1 rounded-full text-xs bg-[#6366f1]/10 text-[#818cf8] border border-[#6366f1]/20">
                {dream.mood}
              </span>
            )}
          </div>

          <p className="text-[#c8d0dc] leading-relaxed mb-4">{dream.content}</p>

          {dream.enhanced_content && (
            <div className="mt-4 p-4 rounded-xl bg-[#0a0a1a]/50 border border-[#6366f1]/10">
              <p className="text-xs text-[#818cf8] mb-2 flex items-center gap-1">
                <Wand2 className="w-3 h-3" /> AI 增强描述
              </p>
              <p className="text-sm text-[#94a3b8] italic">{dream.enhanced_content}</p>
            </div>
          )}

          <div className="flex items-center gap-4 mt-4">
            <span className="text-xs text-[#64748b]">
              {new Date(dream.created_at).toLocaleString("zh-CN")}
            </span>
            {dream.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 rounded-full text-xs bg-[#a855f7]/10 text-[#c084fc]"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Generate Actions */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => handleGenerateImage("surreal")}
            disabled={generating !== null}
            className="dream-button flex items-center gap-2 disabled:opacity-50"
          >
            {generating === "image" ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <ImageIcon className="w-4 h-4" />
            )}
            生成图片
          </button>
          <button
            onClick={() => handleGenerateVideo("dreamlike")}
            disabled={generating !== null}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#a855f7] to-[#ec4899] text-white font-semibold flex items-center gap-2 hover:shadow-lg transition-all disabled:opacity-50"
          >
            {generating === "video" ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Video className="w-4 h-4" />
            )}
            生成视频
          </button>
        </div>

        {/* Generated Images */}
        {images.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-[#6366f1]" />
              梦境图片
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {images.map((gen) => (
                <div key={gen.id} className="glass-card overflow-hidden">
                  {gen.status === "completed" && gen.result_url ? (
                    <div className="relative group">
                      <img
                        src={gen.result_url}
                        alt="Dream visualization"
                        className="w-full aspect-square object-cover"
                      />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <a
                          href={gen.result_url}
                          target="_blank"
                          className="p-3 rounded-full bg-white/20 hover:bg-white/30"
                        >
                          <Download className="w-5 h-5 text-white" />
                        </a>
                      </div>
                    </div>
                  ) : gen.status === "processing" ? (
                    <div className="aspect-square flex items-center justify-center bg-[#0a0a1a]">
                      <div className="text-center">
                        <RefreshCw className="w-8 h-8 text-[#6366f1] animate-spin mx-auto mb-3" />
                        <p className="text-sm text-[#94a3b8]">AI 正在绘制你的梦...</p>
                      </div>
                    </div>
                  ) : (
                    <div className="aspect-square flex items-center justify-center bg-[#0a0a1a]">
                      <p className="text-sm text-red-400">生成失败</p>
                    </div>
                  )}
                  <div className="p-3">
                    <span className="text-xs text-[#64748b]">
                      {gen.style} · {new Date(gen.created_at).toLocaleString("zh-CN")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Generated Videos */}
        {videos.length > 0 && (
          <div>
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Video className="w-5 h-5 text-[#a855f7]" />
              梦境视频
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {videos.map((gen) => (
                <div key={gen.id} className="glass-card overflow-hidden">
                  {gen.status === "completed" && gen.result_url ? (
                    <video
                      src={gen.result_url}
                      controls
                      className="w-full aspect-video"
                      poster=""
                    />
                  ) : gen.status === "processing" ? (
                    <div className="aspect-video flex items-center justify-center bg-[#0a0a1a]">
                      <div className="text-center">
                        <RefreshCw className="w-8 h-8 text-[#a855f7] animate-spin mx-auto mb-3" />
                        <p className="text-sm text-[#94a3b8]">视频生成中，请稍候...</p>
                        <p className="text-xs text-[#64748b] mt-1">通常需要 1-3 分钟</p>
                      </div>
                    </div>
                  ) : (
                    <div className="aspect-video flex items-center justify-center bg-[#0a0a1a]">
                      <p className="text-sm text-red-400">生成失败</p>
                    </div>
                  )}
                  <div className="p-3">
                    <span className="text-xs text-[#64748b]">
                      {gen.style} · {new Date(gen.created_at).toLocaleString("zh-CN")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
