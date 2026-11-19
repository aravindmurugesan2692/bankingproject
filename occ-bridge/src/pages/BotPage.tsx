import { Link } from 'react-router-dom'
import { TeamsBot } from '../components/TeamsBot'
import { TimelinePanel } from '../components/TimelinePanel'
import { useActiveSession } from '../hooks/useAppStore'

export function BotPage() {
  const session = useActiveSession()

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Teams bot</h1>
          <p className="lede">
            Full conversational flow for OCC inside the bridge. Shares live
            session state with the web workspace.
          </p>
        </div>
        {session ? (
          <Link className="ghost link-btn" to="/workspace">
            Open workspace
          </Link>
        ) : null}
      </header>

      <div className="bot-layout">
        <TeamsBot />
        {session ? <TimelinePanel events={session.timeline} compact /> : null}
      </div>
    </div>
  )
}
