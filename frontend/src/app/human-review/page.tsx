"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

interface PendingItem {
  thread_id: string;
  query?: string;
  product_gtin?: string;
}

export default function HumanReviewPage() {
  const t = useTranslations("humanReview");
  const tCommon = useTranslations("common");
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
    const interval = setInterval(fetchPending, 5000);
    return () => clearInterval(interval);
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
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600">{t("description")}</p>
      {loading ? (
        <p className="text-slate-400">{tCommon("loading")}</p>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-slate-400">
          {t("noItems")}
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.thread_id} className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between gap-4">
              <div>
                <p className="font-medium text-slate-800">{item.thread_id}</p>
                <p className="text-sm text-slate-500">{item.query ?? "—"} · GTIN: {item.product_gtin ?? "—"}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(item.thread_id, "approve")}
                  disabled={acting === item.thread_id}
                  className="rounded-lg bg-emerald-500 hover:bg-emerald-600 px-3 py-1 text-sm text-white disabled:opacity-50 transition"
                >
                  {t("approve")}
                </button>
                <button
                  onClick={() => handleAction(item.thread_id, "reject")}
                  disabled={acting === item.thread_id}
                  className="rounded-lg bg-red-500 hover:bg-red-600 px-3 py-1 text-sm text-white disabled:opacity-50 transition"
                >
                  {t("reject")}
                </button>
                <button
                  onClick={() => handleAction(item.thread_id, "modify")}
                  disabled={acting === item.thread_id}
                  className="rounded-lg bg-white border border-slate-200 hover:bg-slate-50 px-3 py-1 text-sm text-slate-700 disabled:opacity-50 transition"
                >
                  {t("modify")}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
