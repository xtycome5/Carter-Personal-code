"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body style={{ background: "#0c0c14", color: "#f0f0f5", fontFamily: "system-ui", padding: "2rem" }}>
        <h2 style={{ color: "#ef4444" }}>Application Error</h2>
        <pre style={{ fontSize: "12px", color: "#9ca3af", background: "#14141f", padding: "1rem", borderRadius: "8px", whiteSpace: "pre-wrap", overflow: "auto" }}>
          {error.message}
          {"\n\n"}
          {error.stack}
        </pre>
        <button onClick={reset} style={{ marginTop: "1rem", padding: "0.5rem 1rem", background: "#7c5cfc", color: "white", border: "none", borderRadius: "8px", cursor: "pointer" }}>
          Try again
        </button>
      </body>
    </html>
  );
}
