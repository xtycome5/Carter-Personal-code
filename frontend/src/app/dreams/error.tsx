"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="main-content min-h-screen flex items-center justify-center p-8">
      <div className="card p-8 max-w-lg w-full text-center">
        <h2 className="text-xl font-bold text-red-400 mb-4">Something went wrong</h2>
        <pre className="text-xs text-[var(--text-muted)] bg-[var(--bg-primary)] p-4 rounded-lg mb-4 overflow-auto text-left whitespace-pre-wrap">
          {error.message}
          {"\n\n"}
          {error.stack}
        </pre>
        <button
          onClick={reset}
          className="btn-primary"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
