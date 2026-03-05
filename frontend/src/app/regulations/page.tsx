"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

interface Version {
  number: string;
  updated_at: string;
}

interface ChangelogEntry {
  version: string;
  date: string;
  changes: string[];
}

interface WatcherStatus {
  updated: boolean;
  changes: string[];
  last_check: string | null;
  error?: string;
  version?: Version;
}

interface RetrainStatus {
  status: string;
  last_run: string | null;
  last_metrics?: Record<string, unknown>;
  last_error?: string;
}

export default function RegulationsPage() {
  const t = useTranslations("regulations");
  const tCommon = useTranslations("common");
  const [version, setVersion] = useState<Version | null>(null);
  const [changelog, setChangelog] = useState<ChangelogEntry[]>([]);
  const [watcher, setWatcher] = useState<WatcherStatus | null>(null);
  const [retrain, setRetrain] = useState<RetrainStatus | null>(null);
  const [loadingVersion, setLoadingVersion] = useState(true);
  const [loadingChangelog, setLoadingChangelog] = useState(true);
  const [loadingWatcher, setLoadingWatcher] = useState(true);
  const [loadingRetrain, setLoadingRetrain] = useState(true);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    api.regulations
      .version()
      .then(setVersion)
      .catch(() => setVersion(null))
      .finally(() => setLoadingVersion(false));
    api.regulations
      .changelog()
      .then(setChangelog)
      .catch(() => setChangelog([]))
      .finally(() => setLoadingChangelog(false));
    api.regulations
      .watcherStatus()
      .then(setWatcher)
      .catch(() => setWatcher(null))
      .finally(() => setLoadingWatcher(false));
    api.regulations
      .retrainStatus()
      .then(setRetrain)
      .catch(() => setRetrain(null))
      .finally(() => setLoadingRetrain(false));
  }, []);

  async function handleForceCheck() {
    setChecking(true);
    try {
      const result = await api.regulations.checkUpdates();
      setWatcher(result as WatcherStatus);
    } catch {
      // keep previous watcher state
    } finally {
      setChecking(false);
    }
  }

  const lastCheck = watcher?.last_check
    ? new Date(watcher.last_check).toLocaleString()
    : t("neverRun");
  const retrainLabel =
    retrain?.status === "running"
      ? t("retrainRunning")
      : retrain?.status === "completed" || retrain?.status === "completed_no_swap"
        ? t("retrainCompleted")
        : retrain?.status === "error"
          ? t("retrainError")
          : t("retrainIdle");

  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
        <p className="mt-1 text-sm text-slate-600">{t("description")}</p>
      </div>

      {/* Version + Last update */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          {t("version")}
        </h3>
        {loadingVersion ? (
          <p className="mt-2 text-slate-500">{tCommon("loading")}</p>
        ) : version ? (
          <div className="mt-2 flex flex-wrap items-baseline gap-4">
            <span className="text-xl font-mono font-semibold text-teal-700">
              {version.number}
            </span>
            <span className="text-sm text-slate-500">
              {t("lastUpdate")}: {version.updated_at ? new Date(version.updated_at).toLocaleString() : "—"}
            </span>
          </div>
        ) : (
          <p className="mt-2 text-amber-600">{tCommon("apiUnavailable")}</p>
        )}
      </section>

      {/* Watcher status + Force check */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          {t("watcherStatus")}
        </h3>
        {loadingWatcher ? (
          <p className="mt-2 text-slate-500">{tCommon("loading")}</p>
        ) : (
          <div className="mt-3 space-y-3">
            <p className="text-sm text-slate-700">
              {t("lastCheck")}: {lastCheck}
            </p>
            {watcher?.error ? (
              <p className="text-sm text-amber-600">{watcher.error}</p>
            ) : null}
            {watcher?.changes?.length ? (
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs font-medium text-slate-500">{t("changes")}</p>
                <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
                  {watcher.changes.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <button
              type="button"
              onClick={handleForceCheck}
              disabled={checking}
              className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
            >
              {checking ? t("checking") : t("forceCheck")}
            </button>
          </div>
        )}
      </section>

      {/* Retrain status */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          {t("retrainStatus")}
        </h3>
        {loadingRetrain ? (
          <p className="mt-2 text-slate-500">{tCommon("loading")}</p>
        ) : (
          <div className="mt-3 space-y-1">
            <p className="text-sm text-slate-700">{retrainLabel}</p>
            {retrain?.last_run ? (
              <p className="text-xs text-slate-500">
                {t("lastCheck")}: {new Date(retrain.last_run).toLocaleString()}
              </p>
            ) : null}
            {retrain?.last_error ? (
              <p className="text-sm text-amber-600">{retrain.last_error}</p>
            ) : null}
          </div>
        )}
      </section>

      {/* Changelog */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          {t("changelog")}
        </h3>
        {loadingChangelog ? (
          <p className="mt-2 text-slate-500">{tCommon("loading")}</p>
        ) : changelog.length === 0 ? (
          <p className="mt-2 text-slate-500">{t("noChangelog")}</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {changelog.map((entry, i) => (
              <li key={i} className="border-l-2 border-teal-200 pl-3">
                <span className="font-mono text-sm font-medium text-teal-700">
                  {entry.version}
                </span>
                <span className="ml-2 text-xs text-slate-500">{entry.date}</span>
                <ul className="mt-1 list-inside list-disc text-sm text-slate-600">
                  {entry.changes?.map((c, j) => (
                    <li key={j}>{c}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
