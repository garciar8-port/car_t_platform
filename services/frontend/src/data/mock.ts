import type {
  Suite, Batch, Patient, Recommendation, ActionCardData,
  KpiData, AuditEntry, EscalationOption, HandoffSection,
} from '../types';

export const suites: Suite[] = [
  { id: 'S1', name: 'Suite 1', status: 'in_use', currentBatch: 'B-1039' },
  { id: 'S2', name: 'Suite 2', status: 'in_use', currentBatch: 'B-1043' },
  { id: 'S3', name: 'Suite 3', status: 'idle' },
  { id: 'S4', name: 'Suite 4', status: 'cleaning' },
  { id: 'S5', name: 'Suite 5', status: 'in_use', currentBatch: 'B-1045' },
  { id: 'S6', name: 'Suite 6', status: 'maintenance' },
];

export const actionCards: ActionCardData[] = [
  {
    id: 'ac1',
    type: 'urgent',
    description: 'QC failure overnight: Batch B-1042 — review re-scheduling plan',
    timeSinceFlag: '6h ago',
    action: 'Review',
    link: '/coordinator/qc-failure/B-1042',
  },
  {
    id: 'ac2',
    type: 'attention',
    description: 'New urgent patient PT-2487 from Memorial Sloan Kettering',
    timeSinceFlag: '2h ago',
    action: 'Review',
    link: '/coordinator/assignment/PT-2487',
  },
  {
    id: 'ac3',
    type: 'info',
    description: 'Suite 4 cleaning cycle complete, ready for next batch',
    timeSinceFlag: '45m ago',
    action: 'View',
    link: '#',
  },
  {
    id: 'ac4',
    type: 'info',
    description: 'Shift handoff note from Sarah (night shift)',
    timeSinceFlag: '1h ago',
    action: 'Read',
    link: '/coordinator/handoff',
  },
  {
    id: 'ac5',
    type: 'urgent',
    description: 'Patient PT-2493 acuity escalated to 0.94 — physician requests expedited slot',
    timeSinceFlag: '30m ago',
    action: 'Escalate',
    link: '/coordinator/escalation/PT-2493',
  },
  {
    id: 'ac6',
    type: 'attention',
    description: 'Cell viability for PT-2471 expires in 4 days — prioritize assignment',
    timeSinceFlag: '3h ago',
    action: 'Assign',
    link: '/coordinator/assignment/PT-2471',
  },
  {
    id: 'ac7',
    type: 'info',
    description: '3 suites idle — 5 patients awaiting assignment',
    timeSinceFlag: 'Now',
    action: 'Assign',
    link: '/coordinator/assignment',
  },
  {
    id: 'ac8',
    type: 'attention',
    description: 'Suite 6 maintenance overdue — ventilation check pending since yesterday',
    timeSinceFlag: '1d ago',
    action: 'View',
    link: '#',
  },
];

export const batches: Batch[] = [
  { id: 'B-1039', patientId: 'PT-2401', suiteId: 'S1', phase: 'Expansion Day 8', status: 'in_progress', startHour: 0, durationHours: 18 },
  { id: 'B-1040', patientId: 'PT-2412', suiteId: 'S1', phase: 'Harvest', status: 'scheduled', startHour: 20, durationHours: 4 },
  { id: 'B-1043', patientId: 'PT-2456', suiteId: 'S2', phase: 'Transduction', status: 'in_progress', startHour: 2, durationHours: 12 },
  { id: 'B-1044', patientId: 'PT-2467', suiteId: 'S2', phase: 'Expansion Day 1', status: 'scheduled', startHour: 16, durationHours: 8 },
  { id: 'B-1046', patientId: 'PT-2478', suiteId: 'S3', phase: 'Awaiting cells', status: 'scheduled', startHour: 8, durationHours: 6 },
  { id: 'B-1041', patientId: 'PT-2445', suiteId: 'S4', phase: 'Cleaning', status: 'blocked', startHour: 0, durationHours: 4 },
  { id: 'B-1047', patientId: 'PT-2489', suiteId: 'S4', phase: 'Activation', status: 'scheduled', startHour: 6, durationHours: 10 },
  { id: 'B-1045', patientId: 'PT-2471', suiteId: 'S5', phase: 'Expansion Day 5', status: 'at_risk', startHour: 0, durationHours: 22 },
  { id: 'B-1048', patientId: 'PT-2490', suiteId: 'S6', phase: 'Maintenance', status: 'blocked', startHour: 0, durationHours: 24 },
];

export const coordinatorKpis: KpiData[] = [
  { label: 'Suite utilization', value: '78%', delta: '7-day trend: stable', status: 'good' },
  { label: 'Patients in queue', value: 12, unit: 'patients', delta: '3 urgent, 7 standard, 2 scheduled', status: 'warning' },
  { label: 'Avg wait time', value: '11.4', unit: 'days', delta: '-0.6 days vs last week', deltaDirection: 'down', status: 'good' },
  { label: 'This week throughput', value: 18, unit: 'batches', target: 'Target: 22', status: 'warning' },
];

export const directorKpis: KpiData[] = [
  { label: 'Throughput', value: 4, unit: 'successful infusions', target: 'Target: 3', status: 'good' },
  { label: 'Avg vein-to-vein time', value: '14.2', unit: 'days', target: 'Target: <15', status: 'good' },
  { label: 'Suite utilization', value: '81%', target: 'Target: 75-85%', status: 'good' },
  { label: 'Batch failure rate', value: '11%', target: 'Target: <12%', status: 'good' },
  { label: 'Open incidents', value: 1, status: 'danger' },
];

export const patientPT2487: Patient = {
  id: 'PT-2487',
  name: 'Patient PT-2487',
  indication: 'DLBCL',
  acuityScore: 0.72,
  sex: 'Female',
  age: 64,
  enrollmentDate: '2026-03-28',
  apheresisDate: '2026-04-08',
  cellsExpectedDate: '2026-04-09',
  targetInfusionWindow: { start: '2026-04-22', end: '2026-04-26' },
  treatmentCenter: 'Memorial Sloan Kettering, NYC',
  bridgingTherapy: 'On bridging therapy until infusion',
  clinicalNotes: 'Patient has had two prior lines of therapy. Disease progression noted on last imaging. Treating physician requests earliest possible slot.',
  priorLines: 2,
  status: 'awaiting_assignment',
  isUrgent: true,
};

export const recommendationPT2487: Recommendation = {
  id: 'rec-001',
  patientId: 'PT-2487',
  recommendedSuiteId: 'S3',
  recommendedSuiteName: 'Suite 3',
  recommendedStartTime: 'In 4 hours',
  confidence: 92,
  status: 'pending',
  alternatives: [
    { suiteId: 'S5', suiteName: 'Suite 5', startTime: 'Tomorrow 8am', confidence: 84, tradeoff: 'Adds 0.8 days wait' },
    { suiteId: 'S2', suiteName: 'Suite 2', startTime: 'In 6 hours', confidence: 78, tradeoff: 'Minor resource conflict' },
  ],
  shapFactors: [
    { factor: 'Suite 3 has the earliest open slot matching this indication\'s typical duration', impact: 'high', direction: 'positive' },
    { factor: 'Patient acuity score (0.72) prioritizes earlier start', impact: 'medium', direction: 'positive' },
    { factor: 'Suite 3 expansion success rate for this indication is 94% historically', impact: 'medium', direction: 'positive' },
  ],
};

export const escalationPT2493: {
  patient: Patient;
  options: EscalationOption[];
  timeline: { date: string; event: string; highlight?: boolean }[];
} = {
  patient: {
    id: 'PT-2493',
    name: 'Patient PT-2493',
    indication: 'ALL',
    acuityScore: 0.94,
    sex: 'Male',
    age: 52,
    enrollmentDate: '2026-04-01',
    apheresisDate: '2026-04-03',
    targetInfusionWindow: { start: '2026-04-10', end: '2026-04-14' },
    treatmentCenter: 'MSKCC',
    status: 'urgent_escalation',
    isUrgent: true,
  },
  options: [
    {
      id: 'opt-a', label: 'Schedule normally',
      estimatedStart: 'April 12 (6 days from now)',
      patientImpact: 'High — patient may not survive wait window',
      patientImpactLevel: 'high',
      operationalImpact: 'Minimal — no schedule changes',
      operationalImpactLevel: 'low',
      confidence: 88, recommended: false,
      badge: 'No recommendation', badgeVariant: 'neutral',
    },
    {
      id: 'opt-b', label: 'Expedite to next available slot',
      estimatedStart: 'April 8 (2 days from now)',
      patientImpact: 'Medium — within survival window',
      patientImpactLevel: 'medium',
      operationalImpact: 'Low — minor delays for 2 other patients (avg 0.4 days)',
      operationalImpactLevel: 'low',
      confidence: 91, recommended: true,
      badge: 'Recommended', badgeVariant: 'success',
    },
    {
      id: 'opt-c', label: 'Preempt current batch in Suite 4',
      estimatedStart: '6 hours from now',
      patientImpact: 'Low — earliest possible',
      patientImpactLevel: 'low',
      operationalImpact: 'High — current batch B-1051 must be discarded, patient PT-2456 will need re-collection',
      operationalImpactLevel: 'high',
      confidence: 76, recommended: false,
      badge: 'High disruption', badgeVariant: 'danger',
    },
  ],
  timeline: [
    { date: 'April 1', event: 'Patient enrolled' },
    { date: 'April 3', event: 'Apheresis completed' },
    { date: 'April 5', event: 'Acuity score 0.71' },
    { date: 'April 6 (today)', event: 'Acuity score 0.94, physician escalation' },
    { date: 'April 14', event: 'Required infusion by', highlight: true },
  ],
};

export const auditEntries: AuditEntry[] = [
  { id: 'aud-1', timestamp: '2026-04-06 07:14', user: 'Maya R.', actionType: 'approve', subject: 'B-1042', details: 'Applied re-scheduling plan after QC failure', justification: 'Minimized patient impact per recommendation', modelVersion: 'v2.3.1', signatureStatus: 'signed' },
  { id: 'aud-2', timestamp: '2026-04-06 06:30', user: 'Maya R.', actionType: 'approve', subject: 'PT-2487', details: 'Assigned to Suite 3, start in 4 hours', modelVersion: 'v2.3.1', signatureStatus: 'signed' },
  { id: 'aud-3', timestamp: '2026-04-05 22:15', user: 'Sarah K.', actionType: 'override', subject: 'PT-2478', details: 'Overrode recommendation: moved from Suite 5 to Suite 3', justification: 'Suite 5 has pending maintenance', modelVersion: 'v2.3.1', signatureStatus: 'signed' },
  { id: 'aud-4', timestamp: '2026-04-05 18:42', user: 'Maya R.', actionType: 'preempt', subject: 'PT-2493', details: 'Expedited to next available slot', justification: 'Patient deteriorating, physician escalation', modelVersion: 'v2.3.1', signatureStatus: 'signed' },
  { id: 'aud-5', timestamp: '2026-04-05 14:20', user: 'System', actionType: 'model_deploy', subject: 'Model v2.3.1', details: 'New model version deployed, trained on 6 months data', modelVersion: 'v2.3.1', signatureStatus: 'na' },
  { id: 'aud-6', timestamp: '2026-04-05 09:10', user: 'David M.', actionType: 'approve', subject: 'Capacity Plan Q2', details: 'Approved 7th suite addition for Q3', modelVersion: 'v2.3.1', signatureStatus: 'signed' },
  { id: 'aud-7', timestamp: '2026-04-04 16:30', user: 'Maya R.', actionType: 'approve', subject: 'PT-2471', details: 'Assigned to Suite 5', modelVersion: 'v2.3.0', signatureStatus: 'signed' },
  { id: 'aud-8', timestamp: '2026-04-04 11:05', user: 'Sarah K.', actionType: 'override', subject: 'PT-2467', details: 'Changed start time from 2pm to 4pm', justification: 'Coordinator availability constraint', modelVersion: 'v2.3.0', signatureStatus: 'signed' },
];

export const handoffSections: HandoffSection[] = [
  {
    title: 'Shift summary',
    content: 'During this shift, 4 batches progressed normally, 1 QC failure was handled with re-scheduling, 2 new patients were assigned, and 1 urgent escalation was approved with expedited scheduling.',
  },
  {
    title: 'Open issues for next shift',
    content: '',
    items: [
      'Suite 6 ventilation maintenance scheduled for 4pm — confirm completed',
      'PT-2487 transduction results expected at 8pm — verify before assigning next batch to Suite 3',
      'Patient PT-2493 expedited start requires 6am verification call to MSKCC',
    ],
  },
  {
    title: 'Decisions made (with rationale)',
    content: '',
    items: [
      'Approved: PT-2487 → Suite 3 (AI recommendation, 92% confidence)',
      'Approved: QC failure re-scheduling plan for B-1042 (minimized patient impact)',
      'Approved: PT-2493 expedited to next available slot (physician escalation)',
    ],
  },
  {
    title: 'Optional notes',
    content: '',
    editable: true,
  },
];

export const patients: Patient[] = [
  {
    id: 'PT-2487', name: 'Patient PT-2487', indication: 'DLBCL', acuityScore: 0.72,
    enrollmentDate: '2026-03-28', apheresisDate: '2026-04-08',
    targetInfusionWindow: { start: '2026-04-22', end: '2026-04-26' },
    treatmentCenter: 'Memorial Sloan Kettering', status: 'awaiting_assignment', isUrgent: true,
  },
  {
    id: 'PT-2493', name: 'Patient PT-2493', indication: 'ALL', acuityScore: 0.94,
    enrollmentDate: '2026-04-01', apheresisDate: '2026-04-03',
    targetInfusionWindow: { start: '2026-04-10', end: '2026-04-14' },
    treatmentCenter: 'MSKCC', status: 'awaiting_assignment', isUrgent: true,
  },
  {
    id: 'PT-2401', name: 'Patient PT-2401', indication: 'DLBCL', acuityScore: 0.58,
    enrollmentDate: '2026-03-15', apheresisDate: '2026-03-20',
    targetInfusionWindow: { start: '2026-04-08', end: '2026-04-12' },
    treatmentCenter: 'MD Anderson', status: 'in_progress', isUrgent: false,
  },
  {
    id: 'PT-2456', name: 'Patient PT-2456', indication: 'MCL', acuityScore: 0.45,
    enrollmentDate: '2026-03-22', apheresisDate: '2026-03-28',
    targetInfusionWindow: { start: '2026-04-14', end: '2026-04-18' },
    treatmentCenter: 'Dana-Farber', status: 'in_progress', isUrgent: false,
  },
  {
    id: 'PT-2471', name: 'Patient PT-2471', indication: 'ALL', acuityScore: 0.81,
    enrollmentDate: '2026-03-25', apheresisDate: '2026-04-01',
    targetInfusionWindow: { start: '2026-04-12', end: '2026-04-16' },
    treatmentCenter: 'Fred Hutchinson', status: 'in_progress', isUrgent: true,
  },
  {
    id: 'PT-2478', name: 'Patient PT-2478', indication: 'DLBCL', acuityScore: 0.33,
    enrollmentDate: '2026-03-30', apheresisDate: '2026-04-05',
    targetInfusionWindow: { start: '2026-04-18', end: '2026-04-22' },
    treatmentCenter: 'City of Hope', status: 'awaiting_assignment', isUrgent: false,
  },
  {
    id: 'PT-2489', name: 'Patient PT-2489', indication: 'FL', acuityScore: 0.27,
    enrollmentDate: '2026-04-02', apheresisDate: '2026-04-07',
    targetInfusionWindow: { start: '2026-04-20', end: '2026-04-24' },
    treatmentCenter: 'Mayo Clinic', status: 'awaiting_assignment', isUrgent: false,
  },
  {
    id: 'PT-2490', name: 'Patient PT-2490', indication: 'DLBCL', acuityScore: 0.61,
    enrollmentDate: '2026-04-03', apheresisDate: '2026-04-08',
    targetInfusionWindow: { start: '2026-04-21', end: '2026-04-25' },
    treatmentCenter: 'Johns Hopkins', status: 'awaiting_assignment', isUrgent: false,
  },
];

export const capacityForecastData = [
  { day: 'Mon', current: 81, projected: 81 },
  { day: 'Tue', current: 78, projected: 83 },
  { day: 'Wed', current: 85, projected: 87 },
  { day: 'Thu', current: 0, projected: 79 },
  { day: 'Fri', current: 0, projected: 82 },
  { day: 'Sat', current: 0, projected: 74 },
  { day: 'Sun', current: 0, projected: 68 },
];

export const throughputSimData = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  current: 3 + Math.sin(i / 5) * 0.8,
  projected: 3.8 + Math.sin(i / 4) * 0.6,
  lower: 3.2 + Math.sin(i / 4) * 0.4,
  upper: 4.4 + Math.sin(i / 4) * 0.8,
}));
