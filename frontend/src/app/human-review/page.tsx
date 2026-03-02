"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";

interface PendingItem {
  thread_id: string;
  query?: string;
  product_gtin?: string;
}

export default function HumanReviewPage() {
  const [items, setItems] = useState<PendingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<string | null>(null);

  function fetchPending() {
    api.humanReview.pending()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchPending();
    const t = setInterval(fetchPending, 5000);
    return () => clearInterval(t);
  }, []);

  async function handleAction(threadId: string, action: string) {
    setActing(threadId);
    try {
      await api.humanReview.action(threadId, action);
      setItems((prev) => prev.filter((i) => i.thread_id !== threadId));
    } finally {
      setActing(null);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-2xl font-semibold">Human review queue (live)</h2>
      <p className="text-slate-400">
        EU AI Act Article 14 – human-in-the-loop for decisions with confidence &lt; 85%. Polls /api/v1/human-review/pending every 5s.
      </p>
      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-slate-700 p-6 text-center text-slate-500">
          No items in queue. When the workflow escalates (confidence 0.70–0.85 or &lt; 0.70), tasks will appear here for approval or override.
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.thread_id} className="rounded-lg border border-slate-700 p-4 flex items-center justify-between gap-4">
              <div>
                <p className="font-medium text-slate-200">{item.thread_id}</p>
                <p className="text-sm text-slate-400">{item.query ?? "—"} · GTIN: {item.product_gtin ?? "—"}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(item.thread_id, "approve")}
                  disabled={acting === item.thread_id}
                  className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-1 text-sm text-white disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleAction(item.thread_id, "reject")}
                  disabled={acting === item.thread_id}
                  className="rounded bg-red-600 hover:bg-red-500 px-3 py-1 text-sm text-white disabled:opacity-50"
                >
                  Reject
                </button>
                <button
                  onClick={() => handleAction(item.thread_id, "modify")}
                  disabled={acting === item.thread_id}
                  className="rounded bg-slate-600 hover:bg-slate-500 px-3 py-1 text-sm text-white disabled:opacity-50"
                >
                  Modify
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
