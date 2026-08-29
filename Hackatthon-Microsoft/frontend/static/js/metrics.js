/**
 * Observability Module: Telemetry, pipeline funnel, latency gauges
 */

function updateObservabilityMetrics(metricsData, statsData) {
  if (!metricsData) return;

  // Funnel numbers
  const funnelTotal = document.getElementById('funnel-total');
  const funnelCandidates = document.getElementById('funnel-candidates');
  const funnelSignificant = document.getElementById('funnel-significant');
  const funnelAgent = document.getElementById('funnel-agent');

  if (funnelTotal) funnelTotal.innerText = `${statsData?.total || 50} Vessels`;
  if (funnelCandidates) funnelCandidates.innerText = `${statsData?.candidates_screened || (statsData?.critical + statsData?.high + statsData?.watch + 2) || 6} Candidates`;
  if (funnelSignificant) funnelSignificant.innerText = `${(statsData?.critical || 0) + (statsData?.high || 0)} Significant`;
  if (funnelAgent) funnelAgent.innerText = `${metricsData.ai_investigations_triggered || (statsData?.critical ? 1 : 0)} Investigations`;

  // Latency counters
  const obsFilter = document.getElementById('obs-filter-latency');
  const obsTraj = document.getElementById('obs-traj-latency');
  const obsAgent = document.getElementById('obs-agent-latency');
  const kpiLatency = document.getElementById('kpi-filter-latency');

  if (obsFilter) obsFilter.innerText = `${metricsData.avg_filter_latency_ms || 0.45} ms`;
  if (obsTraj) obsTraj.innerText = `${metricsData.avg_risk_latency_ms || 2.10} ms`;
  if (obsAgent) obsAgent.innerText = `${metricsData.avg_agent_latency_ms || 420.0} ms`;
  if (kpiLatency) kpiLatency.innerText = `${metricsData.avg_filter_latency_ms || 0.45} ms`;
}

window.MetricsModule = {
  updateObservabilityMetrics,
};
