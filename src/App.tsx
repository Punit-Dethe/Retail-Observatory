import { memo, useCallback, useEffect, useRef, useState, useTransition } from 'react'
import { ArrowDownToLine, ArrowRight, CalendarDays, Check, ChevronDown, Database, ExternalLink, Globe2, LoaderCircle, RotateCcw, X } from 'lucide-react'
import { Empty, number, Segmented } from './components'
import { DashboardSkeleton } from './Loading'
import { Customers, DataLab, Markets, Overview, Products, Sales } from './pages'
import { getPreset, retailMeta } from './presets'
import type { Analytics, Filters, Page } from './types'

const pages: Page[] = ['Overview', 'Sales', 'Customers', 'Products', 'Markets', 'Data lab']
const titles: Record<Page, [string, string]> = {
  Overview: ['The bigger picture.', 'Two years of transactions. A clearer view of what matters.'],
  Sales: ['Every sale has a story.', 'Follow the peaks, the patterns, and the value of every basket.'],
  Customers: ['Get to know your customers.', 'From a first purchase to the habits that bring people back.'],
  Products: ['Find your next bestseller.', 'See what sells, what gets credited, and what belongs together.'],
  Markets: ['A local shop. A wider world.', 'Understand where demand comes from and how markets compare.'],
  'Data lab': ['Behind the numbers.', 'Real data. Clear methods. Insights you can explain.'],
}
const views = { Overview, Sales, Customers, Products, Markets, 'Data lab': DataLab }
const query = new URLSearchParams(window.location.search)
const initialPage = pages.includes(query.get('page') as Page) ? query.get('page') as Page : 'Overview'
const initialFilters = { start: query.get('start') || retailMeta.start, end: query.get('end') || retailMeta.end, country: query.get('country') || 'all' }
const initialData = getPreset(initialFilters)
const visibleDate = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
const sameScope = (a: Filters, b: Filters) => a.start === b.start && a.end === b.end && a.country === b.country

const PageSurface = memo(function PageSurface({ page, data, onNavigate, onCountry, onMonth }: { page: Page; data: Analytics; onNavigate: (page: Page) => void; onCountry: (country: string) => void; onMonth: (month: string) => void }) {
  const View = views[page]
  return <div className="page-content"><View data={data} meta={retailMeta} onNavigate={onNavigate} onCountry={onCountry} onMonth={onMonth} /></div>
})

export default function App() {
  const [page, setPage] = useState<Page>(initialPage)
  const [selectedPage, setSelectedPage] = useState<Page>(initialPage)
  const [isNavigating, startNavigation] = useTransition()
  const [filters, setFilters] = useState<Filters>(initialFilters)
  const [draftStart, setDraftStart] = useState(initialFilters.start)
  const [draftEnd, setDraftEnd] = useState(initialFilters.end)
  const [data, setData] = useState<Analytics | null>(initialData)
  const [loading, setLoading] = useState(!initialData)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [dateError, setDateError] = useState('')
  const [showDates, setShowDates] = useState(false)
  const [slow, setSlow] = useState(false)
  const controller = useRef<AbortController | null>(null)
  const requestId = useRef(0)
  const scope = useRef(filters)
  const busy = !error && (loading || !data || !sameScope(data.filters, filters))

  useEffect(() => {
    // These three views use fixed bundled project values, not fetched or cached results.
    const preset = getPreset(filters)
    if (preset) return
    const request = new AbortController()
    controller.current = request
    const id = ++requestId.current
    setLoading(true)
    const params = new URLSearchParams({ ...filters })
    fetch(`/api/analytics?${params}`, { signal: request.signal }).then(async response => {
      if (!response.ok) { const result = await response.json().catch(() => ({})); throw new Error(result.error || 'We could not calculate this selection.') }
      return response.json()
    }).then(value => {
      if (!request.signal.aborted && id === requestId.current) { setData(value); setLoading(false) }
    }).catch(e => {
      if (e.name !== 'AbortError' && !request.signal.aborted && id === requestId.current) { setError(e.message); setLoading(false) }
    })
    return () => request.abort()
  }, [filters, retry])

  useEffect(() => {
    setSlow(false)
    if (!busy) return
    const timer = window.setTimeout(() => setSlow(true), 5000)
    return () => window.clearTimeout(timer)
  }, [busy, filters])
  useEffect(() => { const params = new URLSearchParams({ ...filters, page: selectedPage }); window.history.replaceState(null, '', `${window.location.pathname}?${params}`) }, [selectedPage, filters])

  const navigate = useCallback((next: Page) => {
    setSelectedPage(next)
    startNavigation(() => setPage(next))
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])
  const changeFilters = useCallback((next: Filters) => {
    if (sameScope(scope.current, next)) return
    // Cancel immediately, before an obsolete custom query can commit a late response.
    controller.current?.abort()
    ++requestId.current
    scope.current = next
    const preset = getPreset(next)
    if (preset) setData(preset)
    setLoading(!preset)
    setError('')
    setFilters(next)
  }, [])
  const updateDates = useCallback((start: string, end: string) => {
    changeFilters({ ...scope.current, start, end })
    setDraftStart(start); setDraftEnd(end); setDateError(''); setShowDates(false)
  }, [changeFilters])
  const selectPreset = (value: string) => value === 'All data' ? updateDates(retailMeta.start, retailMeta.end) : updateDates(`${value}-01-01`, value === '2011' ? retailMeta.end : `${value}-12-31`)
  const preset = filters.start === retailMeta.start && filters.end === retailMeta.end ? 'All data' : filters.start === '2010-01-01' && filters.end === '2010-12-31' ? '2010' : filters.start === '2011-01-01' && filters.end === retailMeta.end ? '2011' : ''
  const country = useCallback((value: string) => changeFilters({ ...scope.current, country: value }), [changeFilters])
  const selectMonth = useCallback((value: string) => {
    const start = `${value}-01`; const date = new Date(`${start}T12:00:00`); date.setMonth(date.getMonth() + 1, 0)
    const end = `${value}-${String(date.getDate()).padStart(2, '0')}`
    updateDates(start < retailMeta.start ? retailMeta.start : start, end > retailMeta.end ? retailMeta.end : end)
  }, [updateDates])
  const reset = () => { changeFilters({ start: retailMeta.start, end: retailMeta.end, country: 'all' }); setDraftStart(retailMeta.start); setDraftEnd(retailMeta.end); setDateError(''); setShowDates(false) }
  const applyDates = (event: React.FormEvent) => {
    event.preventDefault()
    if (!draftStart || !draftEnd) return setDateError('Choose a start and end date.')
    if (draftStart > draftEnd) return setDateError('The start date must be on or before the end date.')
    if (draftStart < retailMeta.start || draftEnd > retailMeta.end) return setDateError(`Choose dates from ${visibleDate(retailMeta.start)} to ${visibleDate(retailMeta.end)}.`)
    updateDates(draftStart, draftEnd)
  }
  const exportCsv = () => {
    if (busy || !data || error) return
    const kind: Record<Page, string> = { Overview: 'trend', Sales: 'transactions', Customers: 'customers', Products: 'products', Markets: 'countries', 'Data lab': 'transactions' }
    const params = new URLSearchParams({ ...filters, kind: kind[page] }); window.location.assign(`/api/export?${params}`)
  }
  const retryRequest = () => { setError(''); setLoading(true); setRetry(value => value + 1) }
  const previousScope = data ? `Showing previous selection: ${data.filters.country === 'all' ? 'All markets' : data.filters.country}, ${visibleDate(data.filters.start)} to ${visibleDate(data.filters.end)}.` : ''
  const status = busy ? slow ? 'Still calculating…' : 'Updating selection…' : isNavigating ? `Opening ${selectedPage}…` : ''
  const hasScope = filters.country !== 'all' || preset === ''

  return <div className="app">
    <a className="skip-link" href="#main-content">Skip to dashboard</a>
    <header className="app-header">
      <button className="brand" onClick={() => navigate('Overview')} aria-label="Retail Observatory overview"><span className="brand-mark" aria-hidden="true"><span /><span /><span /></span><span><strong>retail.</strong><small>OBSERVATORY</small></span></button>
      <nav className="main-nav" aria-label="Dashboard sections">{pages.map(value => <button key={value} className={selectedPage === value ? 'active' : ''} aria-current={selectedPage === value ? 'page' : undefined} onClick={() => navigate(value)}>{value}</button>)}</nav>
      <a className="dataset-button" href="https://archive.ics.uci.edu/dataset/502/online+retail+ii" target="_blank" rel="noreferrer" aria-label="Open Online Retail II source"><Database size={17} /><span>UCI <i>/</i> 02</span><ExternalLink size={12} /></a>
    </header>
    <main id="main-content">
      <div className="page-heading"><div><div className="breadcrumb"><button onClick={() => navigate('Overview')}>Workspace</button><span>/</span><span>{selectedPage}</span></div><h1>{titles[selectedPage][0]}</h1><p>{titles[selectedPage][1]}</p></div><div className="coverage"><i /><div><strong>Online Retail II</strong><span>Historical dataset · 2009–2011</span></div></div></div>
      <section className="filter-bar" aria-label="Dashboard filters">
        <div className="filter-left"><Segmented options={['All data', '2010', '2011']} value={preset} onChange={selectPreset} label="Date preset" /><div className="date-control"><button className={`date-button ${showDates ? 'selected' : ''}`} onClick={() => setShowDates(!showDates)} aria-expanded={showDates} aria-controls="custom-date-panel" aria-label={`Choose date range: ${visibleDate(filters.start)} to ${visibleDate(filters.end)}`}><CalendarDays size={14} /><span>{visibleDate(filters.start)}<span className="date-dash">—</span>{visibleDate(filters.end)}</span><ChevronDown size={13} /></button>{showDates && <form className="date-popover" id="custom-date-panel" onSubmit={applyDates}><div className="date-popover-heading"><strong>Explore a date range</strong><button type="button" className="icon-button" aria-label="Close date picker" onClick={() => setShowDates(false)}><X size={15} /></button></div><label>From<input type="date" value={draftStart} min={retailMeta.start} max={retailMeta.end} onChange={event => setDraftStart(event.target.value)} required /></label><label>Through<input type="date" value={draftEnd} min={retailMeta.start} max={retailMeta.end} onChange={event => setDraftEnd(event.target.value)} required /></label>{dateError && <p className="date-error" role="alert">{dateError}</p>}<button className="button primary" type="submit">Apply dates<Check size={14} /></button></form>}</div></div>
        <div className="filter-right"><label className="country-select"><Globe2 size={15} /><select value={filters.country} onChange={event => country(event.target.value)} aria-label="Filter by country"><option value="all">All markets</option>{retailMeta.countries.map(value => <option key={value}>{value}</option>)}</select></label><button className="button export-button" aria-label="Export CSV" onClick={exportCsv} disabled={!data || busy || isNavigating || Boolean(error)}><ArrowDownToLine size={15} /><span>Export CSV</span></button></div>
        <div className="scope-status-slot"><div className="scope-details" title={`${filters.country === 'all' ? 'All markets' : filters.country} · ${visibleDate(filters.start)} to ${visibleDate(filters.end)}`}>{hasScope && <><span>{filters.country === 'all' ? 'Custom dates' : filters.country} · {visibleDate(filters.start)} to {visibleDate(filters.end)}</span><button onClick={reset} aria-label="Reset filters"><RotateCcw size={10} />Reset</button></>}</div><div className="pending-status" role="status" aria-live="polite" title={busy ? previousScope : status}>{status && <><LoaderCircle size={11} className="spin" /><span>{status}</span><span className="sr-only">{busy ? previousScope : ''}</span></>}</div></div>
      </section>
      <div className="analysis-stage">
        {error ? <div className="error-state" role="alert"><Database size={28} /><h2>The data needs a moment.</h2><p>{error}</p><button className="button primary" onClick={retryRequest}>Try again<RotateCcw size={14} /></button></div> : !data ? <DashboardSkeleton slow={slow} /> : <div className="data-surface" aria-busy={busy || isNavigating} inert={busy || isNavigating}>
          {data.summary.rows === 0 ? <Empty action={<button className="button primary" onClick={reset}>Reset filters<ArrowRight size={14} /></button>} /> : <PageSurface page={page} data={data} onNavigate={navigate} onCountry={country} onMonth={selectMonth} />}
        </div>}
      </div>
      <footer className="app-footer"><span><span className="footer-logo">r.</span>A little more understanding, in every view.</span><div><span>{number(retailMeta.rawRows)} source rows</span><button onClick={() => navigate('Data lab')}>Data & methodology<svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 12 12 4M4 4h8v8" stroke="currentColor" strokeWidth="1.3" /></svg></button></div></footer>
    </main>
  </div>
}
