import type { Recommendation } from '../types'

/**
 * Heuristic AI stub — keyword → team + sample fix steps.
 * Swap point: replace analyzeIssue with a real LLM / triage service later.
 */
export async function analyzeIssue(issue: string): Promise<Recommendation> {
  await delay(550)

  const text = issue.toLowerCase()

  if (matches(text, ['linux', 'kernel', 'ssh', 'cpu', 'memory', 'oom', 'disk', 'systemd', 'host'])) {
    return {
      team: 'Linux',
      summary: 'Symptoms point to a host / OS layer issue. Engage Linux for triage.',
      confidence: 'high',
      steps: [
        'Confirm affected hostname and recent change window',
        'Check CPU, memory, disk, and systemd unit health',
        'Review kernel / syslog around the start of impact',
        'If host is degraded, prepare failover or reboot with change control',
      ],
    }
  }

  if (matches(text, ['network', 'firewall', 'dns', 'latency', 'packet', 'bgp', 'vpn', 'switch', 'router', 'connectivity'])) {
    return {
      team: 'Network',
      summary: 'Symptoms suggest network path or connectivity failure. Engage Network.',
      confidence: 'high',
      steps: [
        'Map source → destination path and recent network changes',
        'Validate DNS resolution and firewall allow rules',
        'Check interface errors, drops, and latency on affected links',
        'Escalate to carrier / WAN if the fault is outside the DC edge',
      ],
    }
  }

  if (matches(text, ['database', 'db', 'sql', 'oracle', 'postgres', 'mysql', 'replication', 'tablespace', 'query', 'deadlock'])) {
    return {
      team: 'Database',
      summary: 'Symptoms align with database performance or availability. Engage Database.',
      confidence: 'high',
      steps: [
        'Identify instance, service name, and primary vs standby',
        'Check session waits, locks, and long-running queries',
        'Validate storage / tablespace headroom',
        'If primary is unhealthy, review failover readiness with DBAs',
      ],
    }
  }

  if (matches(text, ['app', 'application', 'api', 'http', '500', 'timeout', 'deploy', 'release', 'microservice', 'pod', 'k8s'])) {
    return {
      team: 'Application',
      summary: 'Symptoms look application-tier. Engage Application support.',
      confidence: 'medium',
      steps: [
        'Confirm failing endpoints and error rate spike start time',
        'Correlate with recent deploy / config change',
        'Inspect app logs and dependency health (cache, queue, DB)',
        'Consider rollback or traffic shift if a bad release is confirmed',
      ],
    }
  }

  return {
    team: 'Linux',
    summary:
      'No strong keyword match — defaulting to Linux as first-line infrastructure triage.',
    confidence: 'low',
    steps: [
      'Clarify impact scope (users, regions, services)',
      'Gather error messages, hostnames, and start time',
      'Re-run AI triage after more detail is available',
      'Page Linux for initial host health checks if urgency is high',
    ],
  }
}

function matches(text: string, keywords: string[]): boolean {
  return keywords.some((k) => text.includes(k))
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
