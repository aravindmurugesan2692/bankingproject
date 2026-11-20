import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ComingSoonPage } from './pages/ComingSoonPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { DashboardPage } from './pages/DashboardPage'
import { InitiateIncidentPage } from './pages/InitiateIncidentPage'
import { ApprovalsPage } from './pages/ApprovalsPage'
import { BridgesPage } from './pages/BridgesPage'
import { ParticipationPage } from './pages/ParticipationPage'
import { PagerDutyPage } from './pages/PagerDutyPage'
import { ManagementPage } from './pages/ManagementPage'
import { ReportsPage } from './pages/ReportsPage'
import { SettingsPage } from './pages/SettingsPage'
import { SupportTeamsPage } from './pages/SupportTeamsPage'
import { TimelinePage } from './pages/TimelinePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="initiate" element={<InitiateIncidentPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="management" element={<ManagementPage />} />
          <Route path="pagerduty" element={<PagerDutyPage />} />
          <Route path="servicenow" element={<ComingSoonPage />} />
          <Route path="bridges" element={<BridgesPage />} />
          <Route path="participation" element={<ParticipationPage />} />
          <Route path="timeline" element={<TimelinePage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="teams-config" element={<SupportTeamsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
