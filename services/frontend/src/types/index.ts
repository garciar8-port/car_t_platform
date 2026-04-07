export type SuiteStatus = 'idle' | 'in_use' | 'cleaning' | 'maintenance';
export type BatchStatus = 'in_progress' | 'scheduled' | 'at_risk' | 'blocked' | 'completed';
export type Shift = 'morning' | 'afternoon' | 'night';
export type UserRole = 'coordinator' | 'director' | 'qa';
export type ActionCardType = 'urgent' | 'attention' | 'info';
export type KpiStatus = 'good' | 'warning' | 'danger';

export interface Suite {
  id: string;
  name: string;
  status: SuiteStatus;
  currentBatch?: string;
}

export interface Patient {
  id: string;
  name: string;
  indication: string;
  acuityScore: number;
  enrollmentDate: string;
  apheresisDate: string;
  cellsExpectedDate?: string;
  targetInfusionWindow: { start: string; end: string };
  treatmentCenter: string;
  status: string;
  isUrgent: boolean;
  bridgingTherapy?: string;
  clinicalNotes?: string;
  priorLines?: number;
  sex?: string;
  age?: number;
}

export interface Batch {
  id: string;
  patientId: string;
  suiteId: string;
  phase: string;
  status: BatchStatus;
  startHour: number;
  durationHours: number;
  estimatedCompletion?: string;
}

export interface ShapFactor {
  factor: string;
  impact: string;
  direction: 'positive' | 'negative';
}

export interface Alternative {
  suiteId: string;
  suiteName: string;
  startTime: string;
  confidence: number;
  tradeoff: string;
}

export interface Recommendation {
  id: string;
  patientId: string;
  recommendedSuiteId: string;
  recommendedSuiteName: string;
  recommendedStartTime: string;
  confidence: number;
  alternatives: Alternative[];
  shapFactors: ShapFactor[];
  status: 'pending' | 'approved' | 'overridden' | 'rejected';
}

export interface ActionCardData {
  id: string;
  type: ActionCardType;
  description: string;
  timeSinceFlag: string;
  action: string;
  link: string;
}

export interface KpiData {
  label: string;
  value: string | number;
  unit?: string;
  delta?: string;
  deltaDirection?: 'up' | 'down';
  target?: string;
  status: KpiStatus;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  actionType: string;
  subject: string;
  details: string;
  justification?: string;
  modelVersion: string;
  signatureStatus: 'signed' | 'pending' | 'na';
  beforeState?: string;
  afterState?: string;
}

export interface EscalationOption {
  id: string;
  label: string;
  estimatedStart: string;
  patientImpact: string;
  patientImpactLevel: 'low' | 'medium' | 'high';
  operationalImpact: string;
  operationalImpactLevel: 'low' | 'medium' | 'high';
  confidence: number;
  recommended: boolean;
  badge?: string;
  badgeVariant?: 'success' | 'warning' | 'danger' | 'neutral';
}

export interface HandoffSection {
  title: string;
  content: string;
  items?: string[];
  editable?: boolean;
}
