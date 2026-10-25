import { memo, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { colors, money, number, Panel } from './components'
import type { Customer } from './types'

interface PlotPoint { customer: Customer; x: number; y: number }

export const CustomerScatter = memo(function CustomerScatter({ customers }: { customers: Customer[] }) {
  const holder = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const projected = useRef<PlotPoint[]>([])
  const pointerFrame = useRef(0)
  const lastPointer = useRef({ x: 0, y: 0 })
  const [size, setSize] = useState({ width: 0, height: 0, dpr: 1 })
  const [hover, setHover] = useState<PlotPoint | null>(null)
  const description = useId()

  useLayoutEffect(() => {
    const measure = () => {
      if (!holder.current) return
      const { width, height } = holder.current.getBoundingClientRect()
      const dpr = Math.min(3, window.devicePixelRatio || 1)
      setSize(previous => previous.width === width && previous.height === height && previous.dpr === dpr ? previous : { width, height, dpr })
    }
    measure()
    const observer = new ResizeObserver(measure)
    if (holder.current) observer.observe(holder.current)
    window.addEventListener('resize', measure)
    return () => { observer.disconnect(); window.removeEventListener('resize', measure); cancelAnimationFrame(pointerFrame.current) }
  }, [])

  const geometry = useMemo(() => {
    const left = 64, right = 18, top = 13, bottom = 42
    const width = Math.max(1, size.width - left - right)
    const height = Math.max(1, size.height - top - bottom)
    let maxFrequency = 2, minSpend = 1, maxSpend = 10
    const clusters = new Set<number>()
    for (const customer of customers) {
      maxFrequency = Math.max(maxFrequency, customer.frequency)
      minSpend = Math.min(minSpend, customer.monetary)
      maxSpend = Math.max(maxSpend, customer.monetary)
      clusters.add(customer.cluster)
    }
    // Include the full positive monetary domain, including shoppers spending less than £1.
    const minY = Math.pow(10, Math.floor(Math.log10(Math.max(Number.MIN_VALUE, minSpend))))
    const x = (value: number) => left + Math.log10(value) / Math.log10(maxFrequency) * width
    const y = (value: number) => top + (Math.log10(maxSpend) - Math.log10(value)) / (Math.log10(maxSpend) - Math.log10(minY)) * height
    const points = customers.map(customer => ({ customer, x: x(customer.frequency), y: y(customer.monetary) }))
    const xTicks: number[] = []
    let lastX = -Infinity
    for (let power = 0; power <= Math.ceil(Math.log10(maxFrequency)); power++) {
      for (const multiple of [1, 2, 5]) {
        const tick = multiple * Math.pow(10, power)
        if (tick <= maxFrequency && x(tick) - lastX >= (width < 350 ? 40 : 34)) { xTicks.push(tick); lastX = x(tick) }
      }
    }
    const yTicks: number[] = []
    let lastY = Infinity
    for (let power = Math.floor(Math.log10(minY)); power <= Math.ceil(Math.log10(maxSpend)); power++) {
      const tick = Math.pow(10, power)
      if (tick <= maxSpend && lastY - y(tick) >= 26) { yTicks.push(tick); lastY = y(tick) }
    }
    return { left, right, top, bottom, width, height, x, y, xTicks, yTicks, points, clusters: [...clusters].sort((a, b) => a - b) }
  }, [customers, size.width, size.height])

  useEffect(() => {
    const element = canvas.current
    if (!element || !size.width || !size.height) return
    const context = element.getContext('2d')
    if (!context) return
    element.width = Math.round(size.width * size.dpr)
    element.height = Math.round(size.height * size.dpr)
    context.setTransform(size.dpr, 0, 0, size.dpr, 0, 0)
    context.clearRect(0, 0, size.width, size.height)
    context.globalAlpha = .58
    // Every customer is drawn. Clipping to the plot also keeps marks clear of labels.
    context.save()
    context.beginPath()
    context.rect(geometry.left - 4, geometry.top - 4, geometry.width + 8, geometry.height + 8)
    context.clip()
    for (const point of geometry.points) {
      context.beginPath()
      context.fillStyle = colors[point.customer.cluster % colors.length]
      context.arc(point.x, point.y, 2.65, 0, Math.PI * 2)
      context.fill()
    }
    context.restore()
    projected.current = geometry.points
    setHover(null)
  }, [geometry, size])

  const findNearest = () => {
    pointerFrame.current = 0
    let nearest: PlotPoint | null = null, distance = 100
    for (const point of projected.current) {
      const squared = (point.x - lastPointer.current.x) ** 2 + (point.y - lastPointer.current.y) ** 2
      if (squared < distance) { distance = squared; nearest = point }
    }
    setHover(previous => previous?.customer.id === nearest?.customer.id ? previous : nearest)
  }

  return <Panel title="Patterns, discovered" subtitle="K-means clusters · order frequency × positive spend">
    <div className="chart-box customer-scatter" ref={holder} role="img" aria-label={`All ${number(customers.length)} identified customers plotted by order frequency and positive spend on logarithmic axes.`} aria-describedby={description}
      onPointerMove={event => { const bounds = event.currentTarget.getBoundingClientRect(); lastPointer.current = { x: event.clientX - bounds.left, y: event.clientY - bounds.top }; if (!pointerFrame.current) pointerFrame.current = requestAnimationFrame(findNearest) }}
      onPointerLeave={() => { cancelAnimationFrame(pointerFrame.current); pointerFrame.current = 0; setHover(null) }}>
      <canvas ref={canvas} aria-hidden="true" data-point-count={customers.length} />
      <svg className="scatter-axes" width="100%" height="100%" aria-hidden="true">
        {geometry.yTicks.map(tick => <g key={tick}><line x1={geometry.left} y1={geometry.y(tick)} x2={size.width - geometry.right} y2={geometry.y(tick)} stroke="#e5e7e9" strokeDasharray="3 5" /><text x={geometry.left - 10} y={geometry.y(tick) + 3} textAnchor="end">{tick < 1 ? money(tick, false, 2) : money(tick, true)}</text></g>)}
        {geometry.xTicks.map(tick => <text key={tick} x={geometry.x(tick)} y={size.height - 24} textAnchor="middle">{number(tick)}</text>)}
        <text x={geometry.left + geometry.width / 2} y={size.height - 4} textAnchor="middle">Orders · logarithmic scale</text>
      </svg>
      {hover && <><span className="scatter-focus-point" style={{ left: hover.x, top: hover.y }} /><div className="chart-tooltip canvas-tooltip" style={{ left: Math.max(8, Math.min(size.width - 220, hover.x + 13)), top: Math.max(8, Math.min(size.height - 96, hover.y - 38)) }}><strong>Customer #{hover.customer.id}</strong><p>{number(hover.customer.frequency)} orders · {money(hover.customer.monetary, false, 2)}</p><p>{hover.customer.segment}</p></div></>}
    </div>
    <div className="legend-row">{geometry.clusters.map(id => <span className="legend" key={id}><i style={{ background: colors[id % colors.length] }} />Cluster {id + 1}</span>)}</div>
    <p className="scatter-description" id={description}>All customers shown. Hover for details, or use the searchable customer table below for exact values.</p>
  </Panel>
})
