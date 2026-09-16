import { useState } from 'react'
import { checkRequest } from '../api.js'

export default function RequestSimulator() {
  const [clientId, setClientId] = useState('user_123')
  const [algorithm, setAlgorithm] = useState('token_bucket')
  const [limit, setLimit] = useState(10)
  const [windowSeconds, setWindowSeconds] = useState(60)
  const [responses, setResponses] = useState([])
  const [burstSummary, setBurstSummary] = useState(null)

  const currentParams = () => ({
    client_id: clientId,
    algorithm,
    limit: Number(limit),
    window_seconds: Number(windowSeconds),
  })

  const pushResponses = (items) => {
    setResponses((prev) => [...items, ...prev].slice(0, 10))
  }

  const sendRequest = async () => {
    const result = await checkRequest(currentParams())
    setBurstSummary(null)
    pushResponses([result])
  }

  const burstTest = async () => {
    const params = currentParams()
    const results = await Promise.all(Array.from({ length: 20 }, () => checkRequest(params)))
    const allowed = results.filter((r) => r.allowed).length
    const denied = results.length - allowed
    setBurstSummary({ allowed, denied })
    pushResponses(results)
  }

  return (
    <section className="simulator">
      <h2>Request Simulator</h2>
      <div className="simulator-inputs">
        <label>
          Client ID
          <input value={clientId} onChange={(e) => setClientId(e.target.value)} />
        </label>
        <label>
          Algorithm
          <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
            <option value="token_bucket">token_bucket</option>
            <option value="sliding_window">sliding_window</option>
          </select>
        </label>
        <label>
          Limit
          <input type="number" value={limit} onChange={(e) => setLimit(e.target.value)} />
        </label>
        <label>
          Window Seconds
          <input
            type="number"
            value={windowSeconds}
            onChange={(e) => setWindowSeconds(e.target.value)}
          />
        </label>
      </div>
      <div className="simulator-buttons">
        <button onClick={sendRequest}>Send Request</button>
        <button onClick={burstTest}>Burst Test 20x</button>
      </div>
      {burstSummary && (
        <div className="burst-summary">
          <span className="text-green">{burstSummary.allowed} allowed</span>
          {' / '}
          <span className="text-red">{burstSummary.denied} denied</span>
        </div>
      )}
      <div className="response-list">
        {responses.map((r, i) => (
          <div key={i} className={`response-card ${r.allowed ? 'allowed' : 'denied'}`}>
            <span>{r.allowed ? 'ALLOWED' : 'DENIED'}</span>
            <span>remaining: {r.remaining}</span>
            <span>reset in: {r.reset_in_seconds}s</span>
          </div>
        ))}
      </div>
    </section>
  )
}
