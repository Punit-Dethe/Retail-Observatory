import { LoaderCircle } from 'lucide-react'

export function DashboardSkeleton({ slow }: { slow: boolean }) {
  return <div className="loading-state"><div className="loading-label" role="status" aria-live="polite"><LoaderCircle size={17} className="spin" />{slow ? 'Still calculating this selection…' : 'Finding the patterns in your selection…'}</div><div className="skeleton-dashboard" aria-busy="true" aria-hidden="true"><div className="skeleton-metrics">{[0, 1, 2, 3].map(value => <div className="skeleton-placeholder" key={value} />)}</div><div className="skeleton-charts"><div className="skeleton-placeholder" /><div className="skeleton-placeholder" /></div></div></div>
}
