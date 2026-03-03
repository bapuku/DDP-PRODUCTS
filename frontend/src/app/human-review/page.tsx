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
      <h2 className="text-2xl font-semibold">{t("title")}</h2>
      <p className="text-slate-400">{t("description")}</p>
      {loading ? (
        <p className="text-slate-500">{tCommon("loading")}</p>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-slate-700 p-6 text-center text-slate-500">
          {t("noItems")}
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
                  {t("approve")}
                </button>
                <button
                  onClick={() => handleAction(item.thread_id, "reject")}
                  disabled={acting === item.thread_id}
                  className="rounded bg-red-600 hover:bg-red-500 px-3 py-1 text-sm text-white disabled:opacity-50"
                >
                  {t("reject")}
                </button>
                <button
                  onClick={() => handleAction(item.thread_id, "modify")}
                  disabled={acting === item.thread_id}
                  className="rounded bg-slate-600 hover:bg-slate-500 px-3 py-1 text-sm text-white disabled:opacity-50"
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
