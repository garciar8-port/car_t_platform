import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import CoordinatorHomePage from './pages/CoordinatorHomePage';
import PatientAssignmentPage from './pages/PatientAssignmentPage';
import QcFailurePage from './pages/QcFailurePage';
import UrgentEscalationPage from './pages/UrgentEscalationPage';
import HandoffPage from './pages/HandoffPage';
import DirectorHomePage from './pages/DirectorHomePage';
import CapacityPlanningPage from './pages/CapacityPlanningPage';
import AuditTrailPage from './pages/AuditTrailPage';
import MobileCompanionPage from './pages/MobileCompanionPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/coordinator" element={<CoordinatorHomePage />} />
        <Route path="/coordinator/assignment/:patientId" element={<PatientAssignmentPage />} />
        <Route path="/coordinator/qc-failure/:batchId" element={<QcFailurePage />} />
        <Route path="/coordinator/escalation/:patientId" element={<UrgentEscalationPage />} />
        <Route path="/coordinator/handoff" element={<HandoffPage />} />
        <Route path="/director" element={<DirectorHomePage />} />
        <Route path="/director/capacity" element={<CapacityPlanningPage />} />
        <Route path="/audit" element={<AuditTrailPage />} />
        <Route path="/mobile" element={<MobileCompanionPage />} />
      </Routes>
    </BrowserRouter>
  );
}
