"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";

const PHASE_KEYS = [
  "phase0", "phase1", "phase2", "phase3", "phase4",
  "phase5", "phase6", "phase7", "phase8", "phase9",
] as const;

const PHASE_AGENTS: Record<string, { agent: string; label: string }> = {
  phase0: { agent: "data_collection", label: "Data Collection Agent" },
  phase1: { agent: "data_collection", label: "Data Collection Agent" },
  phase2: { agent: "data_collection", label: "Data Collection Agent" },
  phase3: { agent: "data_collection", label: "Data Collection Agent" },
  phase4: { agent: "ddp_generation", label: "DPP Generation Agent" },
  phase5: { agent: "validation", label: "Validation Agent" },
  phase6: { agent: "regulatory_compliance", label: "Regulatory Compliance Agent" },
  phase7: { agent: "human_review", label: "Human Review Agent" },
  phase8: { agent: "audit_trail", label: "Audit Trail Agent" },
  phase9: { agent: "predictive", label: "Predictive Risk Scoring Agent" },
};

type PhaseStatus = "completed" | "current" | "pending";

function getPhaseStatus(index: number, currentPhase: number): PhaseStatus {
  if (index < currentPhase) return "completed";
  if (index === currentPhase) return "current";
  return "pending";
}

const STATUS_STYLES: Record<PhaseStatus, { badge: string; ring: string; label: string }> = {
  completed: {
    badge: "bg-emerald-500 text-white",
    ring: "border-emerald-200 bg-emerald-50/50",
    label: "Completed",
  },
  current: {
    badge: "bg-sky-500 text-white animate-pulse",
    ring: "border-sky-300 bg-sky-50",
    label: "In progress",
  },
  pending: {
    badge: "bg-slate-100 text-slate-500",
    ring: "border-slate-200 bg-white",
    label: "Pending",
  },
};

export default function LifecycleTimelinePage() {
  const t = useTranslations("lifecycle");
  const params = useParams();
  const gtin = params?.gtin as string;
  const serial = params?.serial as string;

  const currentPhase = 4;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/dpp/${gtin}/${serial}`} className="text-sky-500 text-sm hover:text-sky-600 hover:underline">
          {t("backToDpp")}
        </Link>
        <h2 className="text-2xl font-semibold text-slate-800">{t("timelineTitle")}</h2>
      </div>
      <p className="text-slate-600 text-sm">{t("description")}</p>

      {/* Phase progress bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-0.5">
          {PHASE_KEYS.map((_, i) => {
            const status = getPhaseStatus(i, currentPhase);
            return (
              <div
                key={i}
                className={`h-2 flex-1 rounded-full ${
                  status === "completed"
                    ? "bg-emerald-500"
                    : status === "current"
                    ? "bg-sky-500 animate-pulse"
                    : "bg-slate-200"
                }`}
              />
            );
          })}
        </div>
        <p className="text-xs text-slate-500 mt-2 text-center">
          Phase {currentPhase} of {PHASE_KEYS.length - 1} &middot;{" "}
          {currentPhase} completed, 1 in progress, {PHASE_KEYS.length - currentPhase - 1} pending
        </p>
      </div>

      {/* Phase list */}
      <ul className="space-y-2">
        {PHASE_KEYS.map((key, i) => {
          const status = getPhaseStatus(i, currentPhase);
          const styles = STATUS_STYLES[status];
          const agentInfo = PHASE_AGENTS[key];
          return (
            <li
              key={key}
              className={`rounded-xl border p-4 ${styles.ring} transition-colors`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-medium ${styles.badge}`}
                >
                  {status === "completed" ? "✓" : i}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-800">{t(`phases.${key}`)}</span>
                    <span
                      className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                        status === "completed"
                          ? "bg-emerald-100 text-emerald-700"
                          : status === "current"
                          ? "bg-sky-100 text-sky-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {styles.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <Link
                      href={`/agents/${agentInfo.agent}`}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      {agentInfo.label} &rarr;
                    </Link>
                    <Link
                      href={`/dpp/${gtin}/${serial}/lifecycle?trigger=${i}`}
                      className="text-xs text-slate-500 hover:text-sky-600 hover:underline"
                    >
                      Trigger update &rarr;
                    </Link>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
