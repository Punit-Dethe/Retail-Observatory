import { memo, useLayoutEffect, useRef } from 'react'

export type NumberFormat = 'number' | 'money' | 'percent'

export function formatMetric(value: number, format: NumberFormat = 'number', digits = 0) {
  const number = new Intl.NumberFormat('en-GB', format === 'money'
    ? { style: 'currency', currency: 'GBP', minimumFractionDigits: digits, maximumFractionDigits: digits }
    : { minimumFractionDigits: format === 'percent' ? 0 : digits, maximumFractionDigits: digits }).format(value)
  return format === 'percent' ? `${number}%` : number
}

/** Animate the text node only: chart and card trees never render on animation frames. */
export const AnimatedNumber = memo(function AnimatedNumber({ value, format = 'number', digits = 0 }: { value: number; format?: NumberFormat; digits?: number }) {
  const text = useRef<HTMLSpanElement>(null)
  const current = useRef(value)
  const frame = useRef(0)
  useLayoutEffect(() => {
    cancelAnimationFrame(frame.current)
    const startValue = current.current
    const write = (next: number) => { current.current = next; if (text.current) text.current.textContent = formatMetric(next, format, digits) }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || document.hidden || Math.abs(startValue - value) < .00001) {
      write(value)
      return
    }
    write(startValue)
    const start = performance.now()
    const tick = (now: number) => {
      const progress = Math.max(0, Math.min(1, (now - start) / 400))
      const eased = 1 - Math.pow(1 - progress, 3)
      write(progress === 1 ? value : startValue + (value - startValue) * eased)
      if (progress < 1) frame.current = requestAnimationFrame(tick)
    }
    frame.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame.current)
  }, [value, format, digits])
  return <span className="animated-number" aria-label={formatMetric(value, format, digits)}><span ref={text} aria-hidden="true">{formatMetric(value, format, digits)}</span></span>
})
