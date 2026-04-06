import { motion } from 'framer-motion'
import type { StyleInfo } from '../api/types'

export function StyleGrid({
  styles,
  selectedId,
  onSelect,
}: {
  styles: StyleInfo[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {styles.map((s, i) => {
        const active = s.id === selectedId
        return (
          <motion.button
            key={s.id}
            type="button"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            onClick={() => onSelect(s.id)}
            className={`rounded-2xl border px-4 py-3 text-left transition ${
              active
                ? 'border-glam-rose/70 bg-glam-rose/10 ring-2 ring-glam-rose/30'
                : 'border-white/10 bg-zinc-900/50 hover:border-white/20'
            }`}
          >
            <span className="font-display text-base font-semibold text-white">{s.name}</span>
            <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-zinc-400">
              {s.description}
            </p>
          </motion.button>
        )
      })}
    </div>
  )
}
