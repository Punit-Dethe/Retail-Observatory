import { LoaderCircle, Sparkles } from 'lucide-react'
import type { Filters } from './types'

function Skeleton({ className = '', width }: { className?: string; width?: string }) {
  return <span className={`skeleton ${className}`} style={width ? { width } : undefined} />
}

export function DashboardSkeleton({ slow }: { slow: boolean }) {
  return <div className="loading-state">
    <div className="loading-label" role="status" aria-live="polite"><span className="loading-orbit"><Sparkles size={17} /></span><div><strong>{slow ? 'Still calculating this selection…' : 'A clearer picture is on its way.'}</strong><span>{slow ? 'The analysis is still running. You can choose another selection at any time.' : 'Calculating the patterns in your selection.'}</span></div><span className="activity-dots" aria-hidden="true"><i /><i /><i /></span></div>
    <div className="skeleton-dashboard" aria-hidden="true" aria-busy="true">
      <div className="skeleton-metrics">{[0, 1, 2, 3].map(i => <div className={`skeleton-metric skeleton-tone-${i}`} key={i}><Skeleton className="skeleton-label" width="46%" /><Skeleton className="skeleton-value" width={i === 0 ? '81%' : '63%'} /><Skeleton className="skeleton-caption" width="67%" /></div>)}</div>
      <div className="skeleton-charts"><div className="skeleton-chart-panel"><div className="skeleton-chart-header"><Skeleton className="skeleton-label" width="34%" /><Skeleton className="skeleton-pill" /></div><Skeleton className="skeleton-value" width="27%" /><div className="skeleton-plot"><div className="skeleton-gridlines"><i /><i /><i /><i /></div><svg viewBox="0 0 600 170" preserveAspectRatio="none"><path d="M0 145 C35 145 40 100 80 109 S130 135 165 90 S225 120 265 67 S325 102 370 48 S425 75 465 28 S540 65 600 18" fill="none" stroke="currentColor" strokeWidth="3" vectorEffect="non-scaling-stroke" /></svg><span className="skeleton-chart-sweep" /></div><div className="skeleton-axis">{[0, 1, 2, 3, 4, 5].map(i => <Skeleton width="9%" key={i} />)}</div></div><div className="skeleton-insights"><Skeleton className="skeleton-label" width="43%" />{[0, 1, 2].map(i => <div className="skeleton-insight" key={i}><Skeleton className="skeleton-dot" /><div><Skeleton className="skeleton-label" width="72%" /><Skeleton className="skeleton-caption" /><Skeleton className="skeleton-caption" width="83%" /></div></div>)}</div></div>
    </div>
  </div>
}

export function RefreshStatus({ slow, previous }: { slow: boolean; previous: Filters }) {
  const date = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  return <div className="refresh-banner" role="status" aria-live="polite"><span className="refresh-symbol"><LoaderCircle size={17} className="spin" /></span><div><strong>{slow ? 'Still calculating this selection…' : 'Updating your view…'}</strong><span>Showing the previous selection: {previous.country === 'all' ? 'All markets' : previous.country} · {date(previous.start)} – {date(previous.end)}.</span></div><span className="activity-dots" aria-hidden="true"><i /><i /><i /></span><div className="refresh-progress" aria-hidden="true"><i /></div></div>
}
