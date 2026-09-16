export default function HeaderStats({ stats }) {
  const connected = stats.redis_status === 'connected'

  return (
    <section className="header-stats">
      <div className="card">
        <div className="card-label">Total Active Clients</div>
        <div className="card-value">{stats.total_active_clients}</div>
      </div>
      <div className="card">
        <div className="card-label">Requests Last 60s</div>
        <div className="card-value">{stats.requests_last_60s}</div>
      </div>
      <div className="card">
        <div className="card-label">Throttled Last 60s</div>
        <div className={`card-value ${stats.throttled_last_60s > 0 ? 'text-red' : ''}`}>
          {stats.throttled_last_60s}
        </div>
      </div>
      <div className="card">
        <div className="card-label">Redis Status</div>
        <div className="card-value status-value">
          <span className={`dot ${connected ? 'dot-green' : 'dot-red'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
    </section>
  )
}
