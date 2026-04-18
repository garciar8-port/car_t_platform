const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// Types matching backend responses
import type {
  Suite, Patient, Batch, Recommendation,
  ActionCardData, KpiData, AuditEntry,
} from '../types';

export const api = {
  getSuites: () => fetchJson<Suite[]>('/api/v1/suites'),
  getPatientQueue: () => fetchJson<Patient[]>('/api/v1/patients/queue'),
  getPatient: (id: string) => fetchJson<Patient>(`/api/v1/patients/${id}`),
  getBatches: () => fetchJson<Batch[]>('/api/v1/batches'),
  getRecommendation: (patientId: string) =>
    fetchJson<Recommendation>(`/api/v1/recommendations/${patientId}`),
  getCoordinatorKpis: () => fetchJson<KpiData[]>('/api/v1/kpis/coordinator'),
  getDirectorKpis: () => fetchJson<KpiData[]>('/api/v1/kpis/director'),
  getActionCards: () => fetchJson<ActionCardData[]>('/api/v1/action-cards'),
  getAuditTrail: () => fetchJson<AuditEntry[]>('/api/v1/audit'),
  approveRecommendation: (recId: string, user = 'Coordinator', justification?: string) =>
    fetchJson('/api/v1/recommendations/' + recId + '/approve', {
      method: 'POST',
      body: JSON.stringify({ user, justification }),
    }),
  overrideRecommendation: (recId: string, suiteId: string, justification: string, user = 'Coordinator') =>
    fetchJson('/api/v1/recommendations/' + recId + '/override', {
      method: 'POST',
      body: JSON.stringify({ user, selectedSuiteId: suiteId, justification }),
    }),
  stepSimulation: () => fetchJson('/api/v1/simulation/step', { method: 'POST' }),
  health: () => fetchJson<{ status: string; model_version: string; model_loaded: boolean }>('/api/v1/health'),

  flagForReview: (recId: string, user = 'Coordinator') =>
    fetchJson('/api/v1/recommendations/' + recId + '/flag', {
      method: 'POST',
      body: JSON.stringify({ user }),
    }),

  applyReschedule: (batchId: string, user = 'Coordinator') =>
    fetchJson('/api/v1/batches/' + batchId + '/reschedule', {
      method: 'POST',
      body: JSON.stringify({ user, action: 'apply' }),
    }),

  rejectReschedule: (batchId: string, user = 'Coordinator') =>
    fetchJson('/api/v1/batches/' + batchId + '/reschedule', {
      method: 'POST',
      body: JSON.stringify({ user, action: 'reject' }),
    }),

  sendNotifications: (batchId: string, recipients: Record<string, boolean>) =>
    fetchJson('/api/v1/notifications', {
      method: 'POST',
      body: JSON.stringify({ batchId, recipients }),
    }),

  selectEscalationOption: (patientId: string, optionId: string, justification: string, user = 'Coordinator') =>
    fetchJson('/api/v1/escalations/' + patientId + '/select', {
      method: 'POST',
      body: JSON.stringify({ optionId, justification, user }),
    }),

  saveHandoff: (data: { notes: string; checkedItems: Record<string, boolean>; signed: boolean }, user = 'Coordinator') =>
    fetchJson('/api/v1/handoffs', {
      method: 'POST',
      body: JSON.stringify({ ...data, user }),
    }),

  runCapacitySimulation: (params: { suiteCount: number; arrivalRate: number; qcFailRate: number; expansionDuration: number; timeHorizon: number }) =>
    fetchJson<{ throughput: number; avgWait: number; utilization: number; totalInfusions: number; totalFailures: number; failureRate: number }>('/api/v1/capacity/simulate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
};
