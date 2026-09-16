import { useEffect, useState } from 'react'
import AlgorithmExplainer from './components/AlgorithmExplainer.jsx'
import ClientTable from './components/ClientTable.jsx'
import HeaderStats from './components/HeaderStats.jsx'
import RequestSimulator from './components/RequestSimulator.jsx'
import { subscribeToStream } from './api.js'

const INITIAL_STATS = {
  total_active_clients: 0,
  requests_last_60s: 0,
  throttled_last_60s: 0,
  redis_status: 'disconnected',
}

export default function App() {
  const [stats, setStats] = useState(INITIAL_STATS)
  const [clients, setClients] = useState([])

  useEffect(() => {
    const unsubscribe = subscribeToStream((payload) => {
      if (payload.stats) setStats(payload.stats)
      if (payload.clients) setClients(payload.clients)
    })
    return unsubscribe
  }, [])

  return (
    <div className="app">
      <h1>Distributed Rate Limiter Dashboard</h1>
      <HeaderStats stats={stats} />
      <RequestSimulator />
      <ClientTable clients={clients} />
      <AlgorithmExplainer />
    </div>
  )
}
