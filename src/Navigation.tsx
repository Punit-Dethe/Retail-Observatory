import { useLayoutEffect, useRef, useState } from 'react'
import type { Page } from './types'

export const pages: Page[] = ['Overview', 'Sales', 'Customers', 'Products', 'Markets', 'Data lab']

export function Navigation({ page, onChange }: { page: Page; onChange: (page: Page) => void }) {
  const nav = useRef<HTMLElement>(null)
  const [indicator, setIndicator] = useState({ x: 4, width: 0 })
  useLayoutEffect(() => {
    const update = () => { const active = nav.current?.querySelector<HTMLButtonElement>('[aria-current="page"]'); if (active) setIndicator({ x: active.offsetLeft, width: active.offsetWidth }) }
    update()
    const observer = new ResizeObserver(update)
    if (nav.current) observer.observe(nav.current)
    let mounted = true
    document.fonts.ready.then(() => { if (mounted) update() })
    window.addEventListener('resize', update)
    return () => { mounted = false; observer.disconnect(); window.removeEventListener('resize', update) }
  }, [page])
  return <nav ref={nav} className="main-nav" aria-label="Dashboard sections"><span className="nav-indicator" aria-hidden="true" style={{ width: indicator.width, transform: `translateX(${indicator.x}px)` }} />{pages.map(p => <button key={p} className={page === p ? 'active' : ''} aria-current={page === p ? 'page' : undefined} onClick={event => { onChange(p); if (window.innerWidth <= 960) event.currentTarget.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' }) }}>{p}</button>)}</nav>
}
