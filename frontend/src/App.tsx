import { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { fetchStyles, generateMakeup } from './api/client'
import type { GenerateMakeupResponse, StyleInfo } from './api/types'
import { LoadingView } from './components/LoadingView'
import { ResultsTimeline } from './components/ResultsTimeline'
import { StyleGrid } from './components/StyleGrid'

type Phase = 'setup' | 'loading' | 'results'

function App() {
  const [phase, setPhase] = useState<Phase>('setup')
  const [styles, setStyles] = useState<StyleInfo[]>([])
  const [stylesError, setStylesError] = useState<string | null>(null)
  const [selectedStyleId, setSelectedStyleId] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [result, setResult] = useState<GenerateMakeupResponse | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const list = await fetchStyles()
        if (!cancelled) {
          setStyles(list)
          setStylesError(null)
        }
      } catch (e) {
        if (!cancelled) {
          setStylesError(e instanceof Error ? e.message : 'Could not load styles.')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const onPickFile = useCallback((f: File | null) => {
    setFile(f)
    setActionError(null)
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) onPickFile(f)
  }, [onPickFile])

  const runGenerate = useCallback(async () => {
    if (!file || !selectedStyleId) return
    setActionError(null)
    setPhase('loading')
    try {
      const data = await generateMakeup(file, selectedStyleId)
      setResult(data)
      setPhase('results')
    } catch (e) {
      setPhase('setup')
      setActionError(e instanceof Error ? e.message : 'Generation failed.')
    }
  }, [file, selectedStyleId])

  const reset = useCallback(() => {
    setPhase('setup')
    setResult(null)
    setActionError(null)
  }, [])

  const canSubmit = Boolean(file && selectedStyleId && phase === 'setup')

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-16 pt-10 sm:px-8">
      <header className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-glam-rose">Glam AI</p>
          <h1 className="font-display mt-2 text-4xl font-bold text-white sm:text-5xl">
            Masked reveal studio
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-zinc-400">
            One FLUX inpaint for the final look, then Gemini-ordered steps composited with MediaPipe
            masks — background and geometry stay yours.
          </p>
        </div>
        {phase === 'results' && (
          <motion.button
            type="button"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onClick={reset}
            className="rounded-full border border-white/15 bg-white/5 px-5 py-2 text-sm font-medium text-white hover:bg-white/10"
          >
            New session
          </motion.button>
        )}
      </header>

      {stylesError && (
        <div className="mb-6 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          <strong className="font-semibold">Could not load styles.</strong> Run FastAPI (default dev port{' '}
          <code className="rounded bg-black/30 px-1">8001</code>) and ensure{' '}
          <code className="rounded bg-black/30 px-1">CORS_ORIGINS</code> in{' '}
          <code className="rounded bg-black/30 px-1">backend/.env</code> includes this page&apos;s origin
          (e.g. <code className="rounded bg-black/30 px-1">http://localhost:5174</code>). — {stylesError}
        </div>
      )}

      <AnimatePresence mode="wait">
        {phase === 'setup' && (
          <motion.div
            key="setup"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="space-y-10"
          >
            <section className="grid gap-8 lg:grid-cols-2">
              <div>
                <h2 className="font-display text-lg font-semibold text-white">1. Upload selfie</h2>
                <p className="mt-1 text-sm text-zinc-500">JPEG, PNG, or WebP — clear, front-facing face.</p>
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => onPickFile(e.target.files?.[0] ?? null)}
                />
                <div
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
                  }}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={onDrop}
                  onClick={() => inputRef.current?.click()}
                  className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-white/20 bg-zinc-900/40 px-6 py-12 transition hover:border-glam-rose/40 hover:bg-zinc-900/60"
                >
                  {previewUrl ? (
                    <img
                      src={previewUrl}
                      alt="Selected"
                      className="max-h-64 w-full max-w-xs rounded-2xl object-cover shadow-lg"
                    />
                  ) : (
                    <p className="text-center text-sm text-zinc-400">
                      Drop an image here or click to browse
                    </p>
                  )}
                </div>
              </div>

              <div>
                <h2 className="font-display text-lg font-semibold text-white">2. Choose style</h2>
                <p className="mt-1 text-sm text-zinc-500">Fifteen presets — steps are generated per style.</p>
                <div className="mt-4 max-h-[340px] overflow-y-auto pr-1">
                  {styles.length > 0 ? (
                    <StyleGrid
                      styles={styles}
                      selectedId={selectedStyleId}
                      onSelect={(id) => {
                        setSelectedStyleId(id)
                        setActionError(null)
                      }}
                    />
                  ) : (
                    <p className="text-sm text-zinc-500">Loading styles…</p>
                  )}
                </div>
              </div>
            </section>

            {actionError && (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                {actionError}
              </div>
            )}

            <div className="flex justify-center">
              <motion.button
                type="button"
                disabled={!canSubmit}
                whileTap={{ scale: canSubmit ? 0.98 : 1 }}
                onClick={runGenerate}
                className="rounded-full bg-gradient-to-r from-glam-rose to-glam-plum px-10 py-3 text-sm font-semibold text-white shadow-lg shadow-glam-plum/25 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Generate makeup
              </motion.button>
            </div>
          </motion.div>
        )}

        {phase === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="rounded-3xl border border-white/10 bg-zinc-900/30"
          >
            <LoadingView label="Applying your look…" />
          </motion.div>
        )}

        {phase === 'results' && result && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <ResultsTimeline data={result} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
