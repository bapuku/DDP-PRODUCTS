"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import PageAssistant from "@/components/PageAssistant";
import { api } from "@/services/api";

interface PendingItem {
  thread_id: string;
  query?: string;
  product_gtin?: string;
}

const THRESHOLDS = [
  { label: "Auto-approve", range: "≥ 85%", color: "bg-emerald-500", width: "w-[30%]" },
  { label: "Human review", range: "70–84%", color: "bg-amber-400", width: "w-[30%]" },
  { label: "Auto-reject", range: "< 70%", color: "bg-red-500", width: "w-[40%]" },
];

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

      {/* EU AI Act explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-3">
        <h3 className="text-sm font-semibold text-blue-900">EU AI Act Art.&nbsp;14 &mdash; Human Oversight</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          High-risk AI systems must allow effective human oversight. When the multi-agent system
          produces a compliance decision with confidence below 85%, the result is routed here for
          manual review before it can be published or acted upon.
        </p>
        <Link
          href="/agents/human_review"
          className="inline-block text-sm font-medium text-blue-700 hover:text-blue-900 hover:underline"
        >
          Managed by: Human-in-the-Loop Agent &rarr;
        </Link>
      </div>

      {/* Confidence threshold scale */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">Confidence Thresholds</h3>
        <div className="flex h-7 rounded-lg overflow-hidden">
          {THRESHOLDS.map((t) => (
            <div key={t.label} className={`${t.color} ${t.width} flex items-center justify-center`}>
              <span className="text-[11px] font-medium text-white drop-shadow-sm">{t.range}</span>
            </div>
          ))}
        </div>
        <div className="flex text-[11px] text-slate-500">
          <span className="w-[30%] text-center">Auto-approve</span>
          <span className="w-[30%] text-center">Human review</span>
          <span className="w-[40%] text-center">Auto-reject</span>
        </div>
      </div>

      {/* Queue */}
      {loading ? (
        <p className="text-slate-400">{tCommon("loading")}</p>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50">
            <svg className="h-6 w-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-slate-600 font-medium">{t("noItems")}</p>
          <p className="text-sm text-slate-400">
            No items are pending human review. All recent decisions had confidence &ge; 85%.
          </p>
          <div className="flex flex-col items-center gap-1 pt-1">
            <Link href="/dpp/lifecycle/new" className="text-sm text-sky-600 hover:text-sky-700 hover:underline">
              Run a compliance check to trigger the workflow &rarr;
            </Link>
            <Link href="/audit" className="text-sm text-slate-500 hover:text-slate-700 hover:underline">
              View audit trail &rarr;
            </Link>
          </div>
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
      <PageAssistant agentId="human_review" agentLabel="Human Review" pageContext="human-review-queue" />
    </div>
  );
}
