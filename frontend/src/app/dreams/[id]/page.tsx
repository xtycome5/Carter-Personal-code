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
  const hasAnyVideo = videos.length > 0;
  // Show video CTA when image is done but no video has been generated yet
  const showVideoCTA = hasCompletedImage && !hasAnyVideo;

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

        <div className="grid lg:grid-cols-[1fr_320px] gap-8">
          {/* Main content */}
          <div>
            {/* Dream text */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card p-6 mb-6"
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

            {/* Generated Images */}
            {images.length > 0 && (
              <div className="mb-6">
                <h2 className="text-sm font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                  <ImageIcon className="w-4 h-4" /> Images
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
                          <p className="text-xs text-red-400">Failed</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Video generation CTA inline */}
                {showVideoCTA && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="mt-4 p-4 rounded-xl border border-[var(--accent)] bg-[rgba(124,92,252,0.06)] flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#7c5cfc] to-[#c084fc] flex items-center justify-center">
                        <Video className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[var(--text-primary)]">Next step: Animate your dream</p>
                        <p className="text-xs text-[var(--text-muted)]">Turn this painting into a 10-second cinematic video</p>
                      </div>
                    </div>
                    <button
                      onClick={handleGenerateVideo}
                      disabled={generating !== null}
                      className="btn-primary !py-2 !px-4 !text-xs flex items-center gap-1.5 whitespace-nowrap disabled:opacity-40"
                    >
                      <Video className="w-3.5 h-3.5" />
                      Generate Video
                    </button>
                  </motion.div>
                )}
              </div>
            )}

            {/* Generated Videos */}
            {videos.length > 0 && (
              <div>
                <h2 className="text-sm font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                  <Video className="w-4 h-4" /> Videos
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {videos.map((gen) => (
                    <div key={gen.id} className="card overflow-hidden">
                      {gen.status === "completed" && gen.result_url ? (
                        <video
                          src={gen.result_url}
                          controls
                          className="w-full aspect-video"
                        />
                      ) : gen.status === "processing" ? (
                        <div className="aspect-video flex items-center justify-center bg-[var(--bg-elevated)]">
                          <div className="text-center">
                            <RefreshCw className="w-6 h-6 text-[var(--accent)] animate-spin mx-auto mb-2" />
                            <p className="text-xs text-[var(--text-muted)]">Generating video...</p>
                            <p className="text-[10px] text-[var(--text-muted)] mt-1">~2-3 minutes</p>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-video flex items-center justify-center bg-[var(--bg-elevated)]">
                          <p className="text-xs text-red-400">Failed</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Actions */}
          <div className="space-y-4">
            <div className="card p-5">
              <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Generate</h3>
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
                  <div className="relative">
                    {showVideoCTA && (
                      <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-[#7c5cfc] to-[#c084fc] opacity-60 blur-sm animate-pulse" />
                    )}
                    <button
                      onClick={handleGenerateVideo}
                      disabled={generating !== null}
                      className={`relative w-full flex items-center justify-center gap-2 disabled:opacity-40 ${
                        showVideoCTA
                          ? "btn-primary !bg-gradient-to-r !from-[#7c5cfc] !to-[#c084fc]"
                          : "btn-secondary"
                      }`}
                    >
                      {generating === "video" ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Video className="w-4 h-4" />
                      )}
                      {showVideoCTA ? "Bring it to Life — Generate Video" : "Generate Video"}
                    </button>
                  </div>
                )}
              </div>

              {showVideoCTA && (
                <p className="text-xs text-[var(--accent)] mt-3 text-center animate-pulse">
                  Your painting is ready! Turn it into a cinematic video
                </p>
              )}

              {!hasCompletedImage && (
                <p className="text-[10px] text-[var(--text-muted)] mt-3">
                  Generate an image first to unlock video generation
                </p>
              )}
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
