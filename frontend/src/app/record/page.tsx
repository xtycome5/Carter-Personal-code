"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Moon, Save, Image as ImageIcon, Video } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI, generateAPI } from "@/lib/api";

export default function RecordPage() {
  const { token } = useAuthStore();
  const router = useRouter();

  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);
  const [error, setError] = useState("");

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSave = async () => {
    if (!content.trim()) {
      setError("Please describe your dream");
      return;
    }
    setError("");
    setSaving(true);

    try {
      const dream: any = await dreamsAPI.create(token!, {
        title: title || undefined,
        content,
        tags,
      });
      router.push(`/dreams/${dream.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndGenerate = async (type: "image" | "video") => {
    if (!content.trim()) {
      setError("Please describe your dream");
      return;
    }
    setError("");
    setGenerating(type);

    try {
      // Save dream first
      const dream: any = await dreamsAPI.create(token!, {
        title: title || undefined,
        content,
        tags,
      });

      if (type === "image") {
        await generateAPI.image(token!, {
          dream_id: dream.id,
        });
      } else {
        await generateAPI.video(token!, {
          dream_id: dream.id,
          duration: 5,
          resolution: "720P",
        });
      }

      router.push(`/dreams/${dream.id}`);
    } catch (err: any) {
      setError(err.message || "Generation failed");
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Moon className="w-8 h-8 text-[#a855f7]" />
            Record a Dream
          </h1>
          <p className="text-[#94a3b8]">
            Describe your dream in as much detail as possible. AI will visualize it in surreal painterly style.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm text-[#94a3b8] mb-2">Dream Title (optional)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Give this dream a name..."
                className="dream-input"
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm text-[#94a3b8] mb-2">
                Dream Description <span className="text-red-400">*</span>
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Describe your dream... Include scenes, characters, plot, colors, sounds, and other details. For example: I dreamed I was floating on a purple ocean with three moons in the sky..."
                rows={8}
                className="dream-input resize-none"
              />
              <p className="text-xs text-[#64748b] mt-1">
                {content.length} characters - the more detail, the better the result
              </p>
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm text-[#94a3b8] mb-2">Tags</label>
              <div className="flex gap-2 mb-2 flex-wrap">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 rounded-full text-xs bg-[#6366f1]/10 text-[#818cf8] border border-[#6366f1]/20 flex items-center gap-1"
                  >
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      className="hover:text-red-400"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addTag())}
                  placeholder="Add a tag, press Enter to confirm"
                  className="dream-input flex-1"
                />
              </div>
            </div>
          </div>

          {/* Sidebar - Actions Only */}
          <div className="space-y-6">
            {/* Art Style Info */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-medium text-white mb-2">Art Style</h3>
              <p className="text-xs text-[#94a3b8] leading-relaxed">
                All dreams are visualized in a surreal painterly style inspired by
                <span className="text-[#a855f7]"> Dali</span>,
                <span className="text-[#60a5fa]"> Chagall</span>,
                <span className="text-[#34d399]"> Magritte</span> &
                <span className="text-[#f97316]"> Munch</span> —
                melting forms, jewel-toned light, hazy fog, and emotional color.
              </p>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              {error && (
                <p className="text-red-400 text-sm text-center">{error}</p>
              )}

              <button
                onClick={() => handleSaveAndGenerate("image")}
                disabled={generating !== null || saving}
                className="dream-button w-full flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {generating === "image" ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generating Image...
                  </>
                ) : (
                  <>
                    <ImageIcon className="w-4 h-4" />
                    Save & Generate Image
                  </>
                )}
              </button>

              <button
                onClick={() => handleSaveAndGenerate("video")}
                disabled={generating !== null || saving}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-[#a855f7] to-[#ec4899] text-white font-semibold flex items-center justify-center gap-2 hover:shadow-lg transition-all disabled:opacity-50"
              >
                {generating === "video" ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generating Video...
                  </>
                ) : (
                  <>
                    <Video className="w-4 h-4" />
                    Save & Generate Video
                  </>
                )}
              </button>

              <button
                onClick={handleSave}
                disabled={saving || generating !== null}
                className="w-full py-3 rounded-xl border border-[#2a2a5e] text-[#94a3b8] hover:text-white hover:border-[#6366f1] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                Save Only
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
