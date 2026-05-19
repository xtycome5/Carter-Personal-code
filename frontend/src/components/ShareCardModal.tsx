"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { X, Download, Link2, Check } from "lucide-react";
import { toPng } from "html-to-image";

interface ShareCardModalProps {
  open: boolean;
  onClose: () => void;
  dreamContent: string;
  dreamTitle?: string;
  mediaUrl: string;
  mediaType: "image" | "video";
  createdAt: string;
}

export default function ShareCardModal({
  open,
  onClose,
  dreamContent,
  dreamTitle,
  mediaUrl,
  mediaType,
  createdAt,
}: ShareCardModalProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [coverFrame, setCoverFrame] = useState<string | null>(null);
  const [mediaLoaded, setMediaLoaded] = useState(false);

  // Extract video cover frame
  useEffect(() => {
    if (!open || mediaType !== "video" || !mediaUrl) return;
    setCoverFrame(null);
    setMediaLoaded(false);

    const video = document.createElement("video");
    video.crossOrigin = "anonymous";
    video.muted = true;
    video.preload = "auto";

    video.addEventListener("loadeddata", () => {
      // Seek to 1s for a better frame (skip first black frame)
      video.currentTime = Math.min(1, video.duration * 0.1);
    });

    video.addEventListener("seeked", () => {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        setCoverFrame(canvas.toDataURL("image/png"));
        setMediaLoaded(true);
      }
    });

    video.addEventListener("error", () => {
      // Fallback: use video element directly
      setMediaLoaded(true);
    });

    video.src = mediaUrl;
    video.load();

    return () => {
      video.pause();
      video.src = "";
    };
  }, [open, mediaType, mediaUrl]);

  // For images, track load state
  useEffect(() => {
    if (!open || mediaType !== "image") return;
    setMediaLoaded(false);
    setCoverFrame(null);
  }, [open, mediaType]);

  const handleImageLoad = useCallback(() => {
    setMediaLoaded(true);
  }, []);

  const handleSave = async () => {
    if (!cardRef.current) return;
    setSaving(true);
    try {
      // html-to-image needs the images to be loaded and CORS-safe
      const dataUrl = await toPng(cardRef.current, {
        width: 1080,
        height: 1350,
        pixelRatio: 1,
        cacheBust: true,
        fetchRequestInit: { mode: "cors" },
      });
      const link = document.createElement("a");
      link.download = `dream-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error("Failed to export card:", err);
      alert("Export failed. Try downloading the image directly.");
    } finally {
      setSaving(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!open) return null;

  const formattedDate = new Date(createdAt).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  // Truncate dream text for card display
  const displayText =
    dreamContent.length > 120
      ? dreamContent.slice(0, 120) + "..."
      : dreamContent;

  const imageSrc = mediaType === "video" ? coverFrame : mediaUrl;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* Modal content */}
      <div
        className="relative z-10 flex flex-col items-center gap-6 max-h-[90vh] overflow-y-auto p-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-2 right-2 p-2 rounded-full hover:bg-white/10 transition-colors text-white/60 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* === The Card (1080x1350 rendered at 360x450 for preview) === */}
        <div
          style={{
            width: 360,
            height: 450,
            overflow: "hidden",
            borderRadius: 16,
            flexShrink: 0,
          }}
        >
          <div
            ref={cardRef}
            style={{
              width: 1080,
              height: 1350,
              transform: "scale(0.3333)",
              transformOrigin: "top left",
              background: "#0c0c14",
              display: "flex",
              flexDirection: "column",
              fontFamily:
                '"Inter", "SF Pro Display", -apple-system, system-ui, sans-serif',
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Background glow effect */}
            <div
              style={{
                position: "absolute",
                top: -200,
                right: -200,
                width: 600,
                height: 600,
                borderRadius: "50%",
                background:
                  "radial-gradient(circle, rgba(124,92,252,0.08) 0%, transparent 70%)",
                pointerEvents: "none",
              }}
            />

            {/* Main image area — 1080 x 900 */}
            <div
              style={{
                width: 1080,
                height: 900,
                position: "relative",
                overflow: "hidden",
              }}
            >
              {imageSrc ? (
                <img
                  src={imageSrc}
                  crossOrigin="anonymous"
                  onLoad={handleImageLoad}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    display: "block",
                  }}
                />
              ) : (
                <div
                  style={{
                    width: "100%",
                    height: "100%",
                    background: "#1a1a2e",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#6b7280",
                    fontSize: 32,
                  }}
                >
                  {mediaType === "video"
                    ? "Extracting frame..."
                    : "Loading..."}
                </div>
              )}

              {/* Video badge */}
              {mediaType === "video" && (
                <div
                  style={{
                    position: "absolute",
                    top: 36,
                    right: 36,
                    background: "rgba(0,0,0,0.6)",
                    backdropFilter: "blur(8px)",
                    borderRadius: 24,
                    padding: "10px 22px",
                    color: "#fff",
                    fontSize: 26,
                    fontWeight: 600,
                    letterSpacing: "0.5px",
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <span style={{ fontSize: 18 }}>&#9654;</span> VIDEO
                </div>
              )}

              {/* Bottom gradient fade into text area */}
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: 200,
                  background:
                    "linear-gradient(transparent, #0c0c14)",
                  pointerEvents: "none",
                }}
              />
            </div>

            {/* Text area — 1080 x 450 */}
            <div
              style={{
                flex: 1,
                padding: "0 64px 48px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                position: "relative",
                marginTop: -60,
                zIndex: 2,
              }}
            >
              {/* Dream text */}
              <div>
                <p
                  style={{
                    fontSize: 52,
                    lineHeight: 1.45,
                    color: "#f0f0f5",
                    fontWeight: 500,
                    margin: 0,
                    letterSpacing: "0.2px",
                  }}
                >
                  &ldquo;{displayText}&rdquo;
                </p>
              </div>

              {/* Bottom bar: date + logo */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: 40,
                  paddingTop: 32,
                  borderTop: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <span
                  style={{
                    color: "#6b7280",
                    fontSize: 28,
                    fontWeight: 400,
                  }}
                >
                  {formattedDate}
                </span>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 14,
                  }}
                >
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: 10,
                      background:
                        "linear-gradient(135deg, #7c5cfc, #c084fc)",
                    }}
                  />
                  <span
                    style={{
                      color: "#9ca3af",
                      fontSize: 28,
                      fontWeight: 600,
                      letterSpacing: "0.5px",
                    }}
                  >
                    Dream Recorder
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={saving || !mediaLoaded}
            className="btn-primary flex items-center gap-2 disabled:opacity-40"
          >
            {saving ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            {saving ? "Exporting..." : "Save Image"}
          </button>

          <button
            onClick={handleCopyLink}
            className="btn-secondary flex items-center gap-2"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Link2 className="w-4 h-4" />
            )}
            {copied ? "Copied!" : "Copy Link"}
          </button>
        </div>
      </div>
    </div>
  );
}
