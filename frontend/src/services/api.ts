/**
 * DPP Platform API client - typed fetch wrappers for all backend endpoints.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function getLocaleFromCookie(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  const locale = m ? m[1].trim() : "en";
  return locale === "fr" ? "fr" : "en";
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Accept-Language": getLocaleFromCookie(),
    ...(init?.headers as Record<string, string>),
  };
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? err.message ?? "API error");
  }
  return res.json() as Promise<T>;
}

// --- Types ---
export interface ComplianceCheckResult {
  compliance_status: string | null;
  confidence_scores: Record<string, number>;
  requires_human_review: boolean;
  regulation_references: string[];
  final_response: string | null;
}

export interface BatteryPassportResponse {
  dpp_uri: string;
  gtin: string;
  serial_number: string;
  qr_code_data: string | null;
  created_at: string;
  battery_category: string;
  carbon_footprint_class: string;
  chemistry: string | null;
}

export interface DPPSectors {
  sectors: string[];
  regulation_references: string[];
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  agent_id: string;
  decision_type: string;
  confidence_score: number | null;
  regulatory_citations: string[] | null;
  entity_id: string | null;
}

export interface SupplyChainResult {
  gtin: string;
  product?: Record<string, unknown>;
  supply_chain_depth: number;
  upstream_nodes: Record<string, unknown>[];
}

export interface WorkflowRunResult {
  final_response: string | null;
  requires_human_review: boolean;
  confidence_scores: Record<string, number>;
  audit_entries_count: number;
  regulation_references: string[];
}

// --- API functions ---
export const api = {
  health: () => json<{ status: string }>("/health"),
  ready: () => json<{ status: string; checks: Record<string, string> }>("/ready"),

  dpp: {
    sectors: () => json<DPPSectors>("/api/v1/dpp"),
    listBySector: (sector: string, limit = 20) =>
      json<Record<string, unknown>[]>(`/api/v1/dpp/sector/${sector}?limit=${limit}`),
    get: (sector: string, gtin: string, serial: string) =>
      json<Record<string, unknown>>(`/api/v1/dpp/sector/${sector}/${gtin}/${serial}`),
    supplyChain: (gtin: string) =>
      json<SupplyChainResult>(`/api/v1/dpp/sector/supply-chain/${gtin}`),
    create: (body: Record<string, unknown>) =>
      json<{ dpp_uri: string }>("/api/v1/dpp/sector", { method: "POST", body: JSON.stringify(body) }),
  },

  battery: {
    create: (body: Record<string, unknown>) =>
      json<BatteryPassportResponse>("/api/v1/dpp/battery", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    get: (gtin: string, serial: string) =>
      json<Record<string, unknown>>(`/api/v1/dpp/battery/${gtin}/${serial}`),
    qrUrl: (gtin: string, serial: string) =>
      `${BASE}/api/v1/dpp/battery/${gtin}/${serial}/qr`,
  },

  compliance: {
    status: () => json<{ frameworks: string[] }>("/api/v1/compliance/status"),
    check: (query: string, gtin?: string) =>
      json<ComplianceCheckResult>("/api/v1/compliance/check", {
        method: "POST",
        body: JSON.stringify({ query, product_gtin: gtin }),
      }),
  },

  workflow: {
    run: (query: string, gtin?: string, threadId?: string) =>
      json<WorkflowRunResult>("/api/v1/workflow/run", {
        method: "POST",
        body: JSON.stringify({ query, product_gtin: gtin, thread_id: threadId }),
      }),
    pendingReviews: () =>
      json<{ thread_id: string; query?: string; product_gtin?: string }[]>("/api/v1/workflow/pending-reviews"),
  },

  lifecycle: {
    create: (body: { product_gtin: string; serial_number: string; batch_number?: string; query?: string; thread_id?: string }) =>
      json<{ ddp_uri?: string; final_response?: string; requires_human_review?: boolean; ddp_completeness?: number; validation_passed?: boolean; audit_entries_count?: number }>(
        "/api/v1/dpp/lifecycle/create",
        { method: "POST", body: JSON.stringify(body) }
      ),
    update: (gtin: string, serial: string, body: { update_type: string; query?: string; thread_id?: string }) =>
      json<{ final_response?: string; current_phase?: string; audit_entries_count?: number }>(
        `/api/v1/dpp/lifecycle/${gtin}/${serial}/update`,
        { method: "PUT", body: JSON.stringify(body) }
      ),
    audit: (gtin: string, serial: string, threadId?: string) =>
      json<{ audit_report?: Record<string, unknown>; findings_count?: number; corrective_actions?: unknown[]; final_response?: string }>(
        `/api/v1/dpp/audit/${gtin}/${serial}${threadId ? `?thread_id=${threadId}` : ""}`,
        { method: "POST" }
      ),
    carrier: (gtin: string, serial: string) =>
      json<{ qr_data: string; qr_png_base64?: string; qr_svg?: string; nfc_ndef_uri: string; rfid_epc_sgtin96: string }>(
        `/api/v1/dpp/${gtin}/${serial}/carrier`
      ),
    anomalyCheck: (body: { product_gtin?: string; product_data?: Record<string, unknown>; ddp_data?: Record<string, unknown> }) =>
      json<{ anomalies_detected: unknown[]; data_quality_score?: number; count: number }>(
        "/api/v1/dpp/anomaly/check",
        { method: "POST", body: JSON.stringify(body) }
      ),
    auditLog: (params?: { entity_id?: string; agent_id?: string; limit?: number }) => {
      const sp = new URLSearchParams();
      if (params?.entity_id) sp.set("entity_id", params.entity_id);
      if (params?.agent_id) sp.set("agent_id", params.agent_id);
      if (params?.limit) sp.set("limit", String(params.limit));
      return json<AuditEntry[]>(`/api/v1/dpp/audit-log?${sp}`);
    },
  },

  complianceCalendar: () =>
    json<{ year: number; regulation: string; deadline: string; description: string }[]>("/api/v1/compliance/calendar"),

  ml: {
    predictCompliance: (body?: { product_id?: string; weight_kg?: number; carbon_footprint_kg_co2e?: number; circularity_index?: number; ddp_completeness?: number; sector?: string }) =>
      json<{ espr_class?: string; rohs_class?: string; reach_class?: string; carbon_footprint_pred?: number; circularity_pred?: number; compliance_score?: number }>(
        "/api/v1/ml/predict/compliance",
        body ? { method: "POST", body: JSON.stringify(body) } : { method: "GET" }
      ),
    predictComplianceGet: (sector?: string, ddp_completeness?: number) => {
      const sp = new URLSearchParams();
      if (sector) sp.set("sector", sector);
      if (ddp_completeness != null) sp.set("ddp_completeness", String(ddp_completeness));
      return json<Record<string, unknown>>(`/api/v1/ml/predict/compliance?${sp}`);
    },
  },

  humanReview: {
    pending: () => json<{ thread_id: string; query?: string; product_gtin?: string }[]>("/api/v1/human-review/pending"),
    action: (threadId: string, action: string, feedback?: string) =>
      json<{ status: string; action: string; final_response?: string }>(`/api/v1/human-review/${threadId}/action`, {
        method: "POST",
        body: JSON.stringify({ action, feedback }),
      }),
  },

  auth: {
    token: (username: string, password: string): Promise<{ access_token: string }> => {
      const body = new URLSearchParams({ username, password, grant_type: "password" });
      return fetch(`${BASE}/api/v1/auth/token`, {
        method: "POST",
        body,
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "Accept-Language": getLocaleFromCookie(),
        },
      }).then((r) => r.json());
    },
  },
};
