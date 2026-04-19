import type { ErrorRecord, RunRecord } from "@/lib/types";

export function RunHistory({
  runs,
  errors,
}: {
  runs: RunRecord[];
  errors: ErrorRecord[];
}) {
  return (
    <section className="obs-grid">
      <article className="panel stagger">
        <div className="panel-head">
          <h3>Recent Pipeline Runs</h3>
          <span className="pill">OPS</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Status</th>
                <th>Active</th>
                <th>Updated</th>
                <th>Errors</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td>#{r.id}</td>
                  <td>{r.status}</td>
                  <td>{r.active_count}</td>
                  <td>{r.updated_count}</td>
                  <td>{r.error_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
      <article className="panel stagger">
        <div className="panel-head">
          <h3>Recent Errors</h3>
          <span className="pill">DEBUG</span>
        </div>
        <div className="error-list mono">
          {errors.length === 0 ? (
            <p className="status">No recent pipeline errors.</p>
          ) : (
            errors.slice(0, 10).map((e) => (
              <div key={e.id} className="error-item">
                <p>
                  <strong>run #{e.run_id}</strong> / {e.stage}
                </p>
                <p>{e.username ?? "n/a"}</p>
                <p>{e.error.slice(0, 110)}</p>
              </div>
            ))
          )}
        </div>
      </article>
    </section>
  );
}

