export default function AlgorithmExplainer() {
  return (
    <section className="explainer">
      <h2>Algorithms</h2>
      <div className="explainer-cards">
        <div className="explainer-card">
          <h3>Token Bucket</h3>
          <pre>{`[Limit: 10 tokens]
|████████░░| 8/10
Each request consumes 1 token.
Tokens refill over time.
Allows short bursts up to limit.`}</pre>
          <p>
            Good for APIs where occasional bursts are acceptable. Tokens accumulate when
            traffic is low and get spent during spikes.
          </p>
        </div>
        <div className="explainer-card">
          <h3>Sliding Window</h3>
          <pre>{`60 second window
|--[req][req][req][req]--|
     oldest            now
Evicts requests older than window.
Strict limit at all times.`}</pre>
          <p>
            Strict and fair. No bursts allowed beyond the limit. Every request is counted
            within a rolling time window.
          </p>
        </div>
      </div>
    </section>
  )
}
