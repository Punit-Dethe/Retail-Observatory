import type { Analytics, Filters, Meta } from './types'

interface RetailPresets {
  meta: Meta
  generatedAt: string
  sourceSha256: string
  datasets: { all: Analytics; '2010': Analytics; '2011': Analytics }
}

// Vite embeds the source-generated values as inert HTML JSON. Parse once; no fetch,
// browser storage, query cache, or large JavaScript object literal is involved.
const embedded = document.getElementById('retail-presets')
if (!embedded?.textContent) throw new Error('Fixed retail data is missing. Rebuild or restart the local development server.')
const presets = JSON.parse(embedded.textContent) as RetailPresets
export const retailMeta = presets.meta

export function getPreset(filters: Filters): Analytics | null {
  if (filters.country !== 'all') return null
  if (filters.start === retailMeta.start && filters.end === retailMeta.end) return presets.datasets.all
  if (filters.start === '2010-01-01' && filters.end === '2010-12-31') return presets.datasets['2010']
  if (filters.start === '2011-01-01' && filters.end === retailMeta.end) return presets.datasets['2011']
  return null
}
