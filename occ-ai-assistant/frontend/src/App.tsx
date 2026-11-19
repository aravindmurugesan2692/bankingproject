import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ComingSoonPage } from './pages/ComingSoonPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { DashboardPage } from './pages/DashboardPage'
import { InitiateIncidentPage } from './pages/InitiateIncidentPage'
import { ApprovalsPage } from './pages/ApprovalsPage'
import { SupportTeamsPage } from './pages/SupportTeamsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="initiate" element={<InitiateIncidentPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="management" element={<ComingSoonPage />} />
          <Route path="pagerduty" element={<ComingSoonPage />} />
          <Route path="servicenow" element={<ComingSoonPage />} />
          <Route path="bridges" element={<ComingSoonPage />} />
          <Route path="participation" element={<ComingSoonPage />} />
          <Route path="timeline" element={<ComingSoonPage />} />
          <Route path="reports" element={<ComingSoonPage />} />
          <Route path="teams-config" element={<SupportTeamsPage />} />
          <Route path="settings" element={<ComingSoonPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
