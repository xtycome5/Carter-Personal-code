"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Image as ImageIcon, Send } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI, generateAPI } from "@/lib/api";

export default function CreatePage() {
  const { token, user } = useAuthStore();
  const router = useRouter();

  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  // Redirect to auth when unauthenticated user tries to interact
  const requireAuth = () => {
    if (!user) {
      router.push("/auth");
      return true;
    }
    return false;
  };

  const handleGenerate = async () => {
    if (!content.trim()) {
      setError("Describe your dream first");
      return;
    }
    setError("");
    setIsGenerating(true);

    try {
      // Save dream
      const dream: any = await dreamsAPI.create(token!, {
        title: title || undefined,
        content,
      });

      // Generate image
      await generateAPI.image(token!, {
        dream_id: dream.id,
      });

      router.push(`/dreams/${dream.id}`);
    } catch (err: any) {
      setError(err.message || "Generation failed");
      setIsGenerating(false);
    }
  };

  const handleSaveOnly = async () => {
    if (!content.trim()) {
      setError("Describe your dream first");
      return;
    }
    setError("");

    try {
      const dream: any = await dreamsAPI.create(token!, {
        title: title || undefined,
        content,
      });
      router.push(`/dreams/${dream.id}`);
    } catch (err: any) {
      setError(err.message || "Save failed");
    }
  };

  return (
    <div className="main-content">
      <div className="min-h-screen flex flex-col">
        {/* Hero + Input Area */}
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-16 max-w-4xl mx-auto w-full">
          {/* Hero Text */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-3">
              <span className="text-[var(--text-primary)]">Visualize Your </span>
              <span className="bg-gradient-to-r from-[#7c5cfc] to-[#c084fc] bg-clip-text text-transparent">
                Dreams
              </span>
            </h1>
            <p className="text-[var(--text-secondary)] text-lg">
              Describe what you dreamed. AI will paint it in surreal artistry.
            </p>
          </motion.div>

          {/* Input Card */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="w-full"
          >
            <div className="create-input-area">
              {/* Title (optional, collapsed) */}
              <input
                type="text"
                placeholder="Dream title (optional)"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onFocus={() => requireAuth()}
                className="w-full bg-transparent border-none text-[var(--text-primary)] text-sm placeholder:text-[var(--text-muted)] focus:outline-none mb-3 font-medium"
              />

              {/* Main textarea */}
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                onFocus={() => requireAuth()}
                placeholder="Describe your dream in detail... What did you see? What happened? How did it feel?"
                rows={4}
                className="w-full bg-transparent border-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none resize-none text-[15px] leading-relaxed"
              />

              {/* Bottom bar */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border-subtle)]">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[var(--text-muted)]">
                    {content.length} chars
                  </span>
                  {error && (
                    <span className="text-xs text-red-400">{error}</span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSaveOnly}
                    disabled={isGenerating || !content.trim()}
                    className="btn-secondary !py-2 !px-4 !text-xs disabled:opacity-40"
                  >
                    Save Only
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={isGenerating || !content.trim()}
                    className="btn-primary !py-2 !px-5 flex items-center gap-2 disabled:opacity-40"
                  >
                    {isGenerating ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        Generate
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Feature hints */}
          <div className="flex items-center gap-6 mt-6">
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <ImageIcon className="w-3.5 h-3.5" />
              <span>Surreal AI painting</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <Sparkles className="w-3.5 h-3.5" />
              <span>18 master artists pool</span>
            </div>
          </div>
        </div>

        {/* Explore Section - Daily Top 20 */}
        <div className="px-8 pb-16">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">
                Today's Dreams
              </h2>
              <a href="/explore" className="text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors">
                View all
              </a>
            </div>

            {/* Placeholder for gallery - will be populated by API */}
            <div className="gallery-grid">
              {/* Empty state */}
              <div className="col-span-full text-center py-16 text-[var(--text-muted)]">
                <p className="text-sm">Dream gallery coming soon</p>
                <p className="text-xs mt-1">The best dreams of the day will appear here</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
