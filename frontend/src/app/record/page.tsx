"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Moon, Wand2, Save, Image as ImageIcon, Video } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI, generateAPI } from "@/lib/api";

const MOODS = [
  { id: "fantasy", label: "Fantasy", emoji: "✨" },
  { id: "peaceful", label: "Peaceful", emoji: "🌙" },
  { id: "scary", label: "Scary", emoji: "👻" },
  { id: "sad", label: "Sad", emoji: "🌧️" },
  { id: "exciting", label: "Exciting", emoji: "⚡" },
  { id: "romantic", label: "Romantic", emoji: "💫" },
  { id: "mysterious", label: "Mysterious", emoji: "🔮" },
  { id: "nostalgic", label: "Nostalgic", emoji: "🍂" },
];

const STYLES = [
  { id: "surreal", label: "Surrealism", desc: "Dalí-inspired dreamscapes" },
  { id: "watercolor", label: "Watercolor", desc: "Soft, dreamy brush strokes" },
  { id: "cyberpunk", label: "Cyberpunk", desc: "Neon lights & future cities" },
  { id: "classical", label: "Classical", desc: "Renaissance oil painting" },
  { id: "ghibli", label: "Ghibli", desc: "Warm animated world" },
  { id: "gothic", label: "Dark Gothic", desc: "Moonlit mysteries" },
];

export default function RecordPage() {
  const { token } = useAuthStore();
  const router = useRouter();

  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [mood, setMood] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [selectedStyle, setSelectedStyle] = useState("surreal");
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
        mood: mood || undefined,
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
        mood: mood || undefined,
        tags,
      });

      if (type === "image") {
        // Generate image
        await generateAPI.image(token!, {
          dream_id: dream.id,
          style: selectedStyle,
        });
      } else {
        // Generate video (T2V since no image exists yet)
        await generateAPI.video(token!, {
          dream_id: dream.id,
          style: selectedStyle,
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
            Describe your dream in as much detail as possible. AI will visualize it for you.
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

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Mood */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-medium text-white mb-3">Mood</h3>
              <div className="grid grid-cols-2 gap-2">
                {MOODS.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setMood(mood === m.id ? "" : m.id)}
                    className={`px-3 py-2 rounded-lg text-xs transition-all ${
                      mood === m.id
                        ? "bg-[#6366f1]/20 border border-[#6366f1]/50 text-white"
                        : "border border-[#2a2a5e] text-[#94a3b8] hover:border-[#6366f1]/30"
                    }`}
                  >
                    {m.emoji} {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Style */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-medium text-white mb-3">Art Style</h3>
              <div className="space-y-2">
                {STYLES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setSelectedStyle(s.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all ${
                      selectedStyle === s.id
                        ? "bg-[#6366f1]/20 border border-[#6366f1]/50 text-white"
                        : "border border-[#2a2a5e] text-[#94a3b8] hover:border-[#6366f1]/30"
                    }`}
                  >
                    <div className="font-medium">{s.label}</div>
                    <div className="text-[#64748b]">{s.desc}</div>
                  </button>
                ))}
              </div>
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
