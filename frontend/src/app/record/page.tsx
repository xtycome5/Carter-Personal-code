"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Moon, Wand2, Save } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { dreamsAPI, generateAPI } from "@/lib/api";

const MOODS = [
  { id: "fantasy", label: "奇幻", emoji: "✨" },
  { id: "peaceful", label: "平静", emoji: "🌙" },
  { id: "scary", label: "恐怖", emoji: "👻" },
  { id: "sad", label: "悲伤", emoji: "🌧️" },
  { id: "exciting", label: "刺激", emoji: "⚡" },
  { id: "romantic", label: "浪漫", emoji: "💫" },
  { id: "mysterious", label: "神秘", emoji: "🔮" },
  { id: "nostalgic", label: "怀旧", emoji: "🍂" },
];

const STYLES = [
  { id: "surreal", label: "超现实主义", desc: "达利风格的梦幻世界" },
  { id: "watercolor", label: "水彩梦幻", desc: "柔和的水彩画风" },
  { id: "cyberpunk", label: "赛博朋克", desc: "霓虹灯与未来城市" },
  { id: "classical", label: "古典油画", desc: "文艺复兴风格" },
  { id: "ghibli", label: "宫崎骏风", desc: "温暖的动画世界" },
  { id: "gothic", label: "暗黑哥特", desc: "月光下的神秘" },
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
  const [generating, setGenerating] = useState(false);
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
      setError("请描述你的梦境");
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
      setError(err.message || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndGenerate = async () => {
    if (!content.trim()) {
      setError("请描述你的梦境");
      return;
    }
    setError("");
    setGenerating(true);

    try {
      // 先保存梦境
      const dream: any = await dreamsAPI.create(token!, {
        title: title || undefined,
        content,
        mood: mood || undefined,
        tags,
      });

      // AI 增强描述
      await generateAPI.enhance(token!, {
        dream_id: dream.id,
        style: selectedStyle,
      });

      // 生成图片
      await generateAPI.image(token!, {
        dream_id: dream.id,
        style: selectedStyle,
      });

      router.push(`/dreams/${dream.id}`);
    } catch (err: any) {
      setError(err.message || "生成失败");
    } finally {
      setGenerating(false);
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
            记录梦境
          </h1>
          <p className="text-[#94a3b8]">
            尽可能详细地描述你的梦境，AI 会帮你将它可视化
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm text-[#94a3b8] mb-2">梦境标题（可选）</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="给这个梦起个名字..."
                className="dream-input"
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm text-[#94a3b8] mb-2">
                梦境描述 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="描述你的梦境...尽可能包含场景、人物、情节、颜色、声音等细节。例如：我梦见自己在一片紫色的海洋上漂浮，天空中有三个月亮..."
                rows={8}
                className="dream-input resize-none"
              />
              <p className="text-xs text-[#64748b] mt-1">
                {content.length} 字 · 描述越详细，生成效果越好
              </p>
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm text-[#94a3b8] mb-2">标签</label>
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
                  placeholder="添加标签，回车确认"
                  className="dream-input flex-1"
                />
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Mood */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-medium text-white mb-3">情绪基调</h3>
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
              <h3 className="text-sm font-medium text-white mb-3">生成风格</h3>
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
                onClick={handleSaveAndGenerate}
                disabled={generating || saving}
                className="dream-button w-full flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    AI 生成中...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" />
                    保存并生成图片
                  </>
                )}
              </button>

              <button
                onClick={handleSave}
                disabled={saving || generating}
                className="w-full py-3 rounded-xl border border-[#2a2a5e] text-[#94a3b8] hover:text-white hover:border-[#6366f1] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                仅保存
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
