export default function ClientTable({ clients }) {
  return (
    <section className="client-table">
      <h2>Live Clients</h2>
      {clients.length === 0 ? (
        <p className="empty-state">No active clients. Use the simulator above to generate traffic.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Client ID</th>
              <th>Algorithm</th>
              <th>Requests in Window</th>
              <th>Remaining</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.client_id} className={c.is_throttled ? 'row-throttled' : ''}>
                <td>{c.client_id}</td>
                <td>{c.algorithm}</td>
                <td>{c.requests_in_window}</td>
                <td>{c.remaining}</td>
                <td>
                  <span className={`badge ${c.is_throttled ? 'badge-red' : 'badge-green'}`}>
                    {c.is_throttled ? 'Throttled' : 'OK'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
