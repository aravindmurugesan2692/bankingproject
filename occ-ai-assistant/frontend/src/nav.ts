import type { LucideIcon } from 'lucide-react'
import {
  Activity,
  BarChart3,
  Bell,
  ClipboardCheck,
  FileText,
  Headset,
  LayoutDashboard,
  ListChecks,
  Network,
  PlusCircle,
  Settings,
  ShieldAlert,
  Users,
} from 'lucide-react'

export type NavItem = {
  label: string
  path: string
  icon: LucideIcon
  phaseReady: boolean
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard, phaseReady: true },
  { label: 'Initiate Incident', path: '/initiate', icon: PlusCircle, phaseReady: true },
  { label: 'Incident Analysis', path: '/analysis', icon: BarChart3, phaseReady: true },
  { label: 'Incident Approvals', path: '/approvals', icon: ClipboardCheck, phaseReady: true },
  { label: 'Incident Management', path: '/management', icon: ListChecks, phaseReady: true },
  { label: 'PagerDuty', path: '/pagerduty', icon: Bell, phaseReady: true },
  { label: 'ServiceNow', path: '/servicenow', icon: ShieldAlert, phaseReady: false },
  { label: 'Teams Bridge Management', path: '/bridges', icon: Headset, phaseReady: true },
  { label: 'Team Participation', path: '/participation', icon: Users, phaseReady: true },
  { label: 'Incident Timeline', path: '/timeline', icon: Activity, phaseReady: true },
  { label: 'AI Incident Reports', path: '/reports', icon: FileText, phaseReady: true },
  { label: 'Support Team Configuration', path: '/teams-config', icon: Network, phaseReady: true },
  { label: 'Settings', path: '/settings', icon: Settings, phaseReady: true },
]
