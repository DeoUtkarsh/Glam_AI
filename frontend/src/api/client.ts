import type { GenerateMakeupResponse, StyleInfo } from './types'

/** Default Glam AI API port in dev (8000/5173 are often already in use). */
const DEFAULT_DEV_API_ORIGIN = 'http://127.0.0.1:8001'

/**
 * In dev, call FastAPI directly (no Vite proxy). Set `VITE_API_URL` in `frontend/.env` if your API
 * uses another host/port. Production: set `VITE_API_URL` or leave empty for same-origin.
 */
function apiBase(): string {
  const fromEnv = (import.meta.env.VITE_API_URL as string | undefined)?.trim().replace(/\/$/, '')
  if (fromEnv) return fromEnv
  if (import.meta.env.DEV) return DEFAULT_DEV_API_ORIGIN
  return ''
}

async function parseError(res: Response): Promise<string> {
  try {
    const j: unknown = await res.json()
    if (j && typeof j === 'object' && 'detail' in j) {
      const d = (j as { detail: unknown }).detail
      if (typeof d === 'string') return d
      if (Array.isArray(d)) {
        const parts = d
          .map((x) =>
            x && typeof x === 'object' && 'msg' in x ? String((x as { msg: unknown }).msg) : '',
          )
          .filter(Boolean)
        if (parts.length) return parts.join('; ')
      }
    }
    if (j && typeof j === 'object' && 'message' in j) {
      const m = (j as { message: unknown }).message
      if (typeof m === 'string') return m
    }
  } catch {
    /* ignore */
  }
  return res.statusText || `HTTP ${res.status}`
}

export async function fetchStyles(): Promise<StyleInfo[]> {
  const base = apiBase()
  const res = await fetch(`${base}/api/styles`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function generateMakeup(
  file: File,
  styleId: string,
): Promise<GenerateMakeupResponse> {
  const base = apiBase()
  const body = new FormData()
  body.append('image', file)
  body.append('style_id', styleId)
  const res = await fetch(`${base}/api/generate-makeup`, {
    method: 'POST',
    body,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export function pngDataUrl(base64: string): string {
  return `data:image/png;base64,${base64}`
}
