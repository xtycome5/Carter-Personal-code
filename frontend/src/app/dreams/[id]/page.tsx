"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Image as ImageIcon,
  Video,
  Wand2,
  RefreshCw,
  Download,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI, generateAPI } from "@/lib/api";

interface Generation {
  id: string;
  type: "image" | "video";
  status: string;
  result_url?: string;
  created_at: string;
}

interface Dream {
  id: string;
  title?: string;
  content: string;
  enhanced_content?: string;
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
    if (token && dreamId) loadDream();
  }, [token, dreamId]);

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
            loadDream();
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

  const handleGenerateImage = async () => {
    if (!dream) return;
    setGenerating("image");
    try {
      const gen: any = await generateAPI.image(token!, { dream_id: dream.id });
      setPolling((prev) => new Set(prev).add(gen.id));
      loadDream();
    } catch (err: any) {
      alert(err.message || "Generation failed");
    } finally {
      setGenerating(null);
    }
  };

  const handleGenerateVideo = async () => {
    if (!dream) return;
    setGenerating("video");
    try {
      const gen: any = await generateAPI.video(token!, {
        dream_id: dream.id,
        duration: 10,
        resolution: "720P",
      });
      setPolling((prev) => new Set(prev).add(gen.id));
      loadDream();
    } catch (err: any) {
      alert(err.message || "Generation failed");
    } finally {
      setGenerating(null);
    }
  };

  if (loading) {
    return (
      <div className="main-content min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!dream) {
    return (
      <div className="main-content min-h-screen flex items-center justify-center text-[var(--text-muted)]">
        Dream not found
      </div>
    );
  }

  const images = dream.generations.filter((g) => g.type === "image");
  const videos = dream.generations.filter((g) => g.type === "video");
  const hasCompletedImage = images.some((g) => g.status === "completed" && g.result_url);

  return (
    <div className="main-content min-h-screen px-8 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Back link */}
        <Link
          href="/dreams"
          className="inline-flex items-center gap-2 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dreams
        </Link>

        {/* ===== TOP: Media (Images left + Videos right, side by side) ===== */}
        <div className="mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Left: Image panel */}
            <div>
              <h2 className="text-sm font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" /> Image
              </h2>
              {images.length > 0 ? (
                <div className="space-y-3">
                  {images.map((gen) => (
                    <div key={gen.id} className="card overflow-hidden">
                      {gen.status === "completed" && gen.result_url ? (
                        <div className="relative group">
                          <img
                            src={gen.result_url}
                            alt="Dream visualization"
                            className="w-full aspect-square object-cover"
                          />
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                            <a
                              href={gen.result_url}
                              target="_blank"
                              className="p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
                            >
                              <Download className="w-5 h-5 text-white" />
                            </a>
                          </div>
                        </div>
                      ) : gen.status === "processing" ? (
                        <div className="aspect-square flex items-center justify-center bg-[var(--bg-elevated)]">
                          <div className="text-center">
                            <RefreshCw className="w-6 h-6 text-[var(--accent)] animate-spin mx-auto mb-2" />
                            <p className="text-xs text-[var(--text-muted)]">Painting your dream...</p>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-square flex items-center justify-center bg-[var(--bg-elevated)]">
                          <p className="text-xs text-red-400">Generation failed</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                /* No image yet — generate CTA */
                <div className="card aspect-square flex flex-col items-center justify-center text-center">
                  <ImageIcon className="w-10 h-10 text-[var(--text-muted)] mb-3 opacity-40" />
                  <p className="text-sm text-[var(--text-muted)] mb-4">Generate a dream painting</p>
                  <button
                    onClick={handleGenerateImage}
                    disabled={generating !== null}
                    className="btn-primary flex items-center gap-2 disabled:opacity-40"
                  >
                    {generating === "image" ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Wand2 className="w-4 h-4" />
                    )}
                    Generate Image
                  </button>
                </div>
              )}
            </div>

            {/* Right: Video panel (always visible) */}
            <div>
              <h2 className="text-sm font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                <Video className="w-4 h-4" /> Video
              </h2>
              {videos.length > 0 ? (
                <div className="space-y-3">
                  {videos.map((gen) => (
                    <div key={gen.id} className="card overflow-hidden">
                      {gen.status === "completed" && gen.result_url ? (
                        <video
                          src={gen.result_url}
                          controls
                          className="w-full aspect-square object-cover"
                        />
                      ) : gen.status === "processing" ? (
                        <div className="aspect-square flex items-center justify-center bg-[var(--bg-elevated)]">
                          <div className="text-center">
                            <RefreshCw className="w-6 h-6 text-[var(--accent)] animate-spin mx-auto mb-2" />
                            <p className="text-xs text-[var(--text-muted)]">Generating video...</p>
                            <p className="text-[10px] text-[var(--text-muted)] mt-1">~2-3 minutes</p>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-square flex items-center justify-center bg-[var(--bg-elevated)]">
                          <p className="text-xs text-red-400">Generation failed</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                /* No video yet — show CTA inside the frame */
                <div className="card aspect-square flex flex-col items-center justify-center text-center border-dashed border-[var(--border-subtle)]">
                  {hasCompletedImage ? (
                    <>
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#7c5cfc]/20 to-[#c084fc]/20 flex items-center justify-center mb-3">
                        <Video className="w-6 h-6 text-[var(--accent)]" />
                      </div>
                      <p className="text-sm font-medium text-[var(--text-primary)] mb-1">Bring it to life</p>
                      <p className="text-xs text-[var(--text-muted)] mb-4 max-w-[200px]">
                        Animate your painting into a 10s cinematic video
                      </p>
                      <button
                        onClick={handleGenerateVideo}
                        disabled={generating !== null}
                        className="btn-primary flex items-center gap-2 disabled:opacity-40"
                      >
                        {generating === "video" ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Video className="w-4 h-4" />
                        )}
                        Generate Video
                      </button>
                    </>
                  ) : (
                    <>
                      <Video className="w-10 h-10 text-[var(--text-muted)] mb-3 opacity-30" />
                      <p className="text-xs text-[var(--text-muted)] max-w-[180px]">
                        Generate an image first to unlock video
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ===== BOTTOM: User Input + Prompts + Actions ===== */}
        <div className="grid lg:grid-cols-[1fr_320px] gap-8">
          {/* Dream text + enhanced content */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="card p-6"
          >
            <h1 className="text-xl font-bold text-[var(--text-primary)] mb-3">
              {dream.title || "Untitled Dream"}
            </h1>
            <p className="text-[var(--text-secondary)] leading-relaxed text-[15px]">
              {dream.content}
            </p>

            {dream.enhanced_content && (
              <div className="mt-5 p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                <p className="text-xs text-[var(--accent)] mb-2 flex items-center gap-1.5 font-medium">
                  <Wand2 className="w-3 h-3" /> AI Creative Brief
                </p>
                <p className="text-sm text-[var(--text-muted)] italic leading-relaxed">
                  {dream.enhanced_content}
                </p>
              </div>
            )}

            <div className="flex items-center gap-3 mt-4 pt-4 border-t border-[var(--border-subtle)]">
              <span className="text-xs text-[var(--text-muted)]">
                {new Date(dream.created_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </span>
              {dream.tags?.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-md text-[10px] bg-[var(--accent-glow)] text-[var(--accent)]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Sidebar - Actions */}
          <div className="space-y-4">
            <div className="card p-5">
              <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Regenerate</h3>
              <div className="space-y-2">
                <button
                  onClick={handleGenerateImage}
                  disabled={generating !== null}
                  className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-40"
                >
                  {generating === "image" ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <ImageIcon className="w-4 h-4" />
                  )}
                  {hasCompletedImage ? "Regenerate Image" : "Generate Image"}
                </button>

                {hasCompletedImage && (
                  <button
                    onClick={handleGenerateVideo}
                    disabled={generating !== null}
                    className="btn-secondary w-full flex items-center justify-center gap-2 disabled:opacity-40"
                  >
                    {generating === "video" ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Video className="w-4 h-4" />
                    )}
                    Regenerate Video
                  </button>
                )}
              </div>
            </div>

            {/* Info */}
            <div className="card p-5">
              <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">About</h3>
              <div className="space-y-2 text-xs text-[var(--text-muted)]">
                <div className="flex justify-between">
                  <span>Images</span>
                  <span className="text-[var(--text-secondary)]">{images.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>Videos</span>
                  <span className="text-[var(--text-secondary)]">{videos.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span className="text-[var(--text-secondary)]">
                    {new Date(dream.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
