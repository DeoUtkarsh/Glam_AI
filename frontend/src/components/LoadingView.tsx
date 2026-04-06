import { motion } from 'framer-motion'

export function LoadingView({ label }: { label: string }) {
  return (
    <div className="flex min-h-[420px] flex-col items-center justify-center gap-10 px-6 py-16">
      <div className="relative h-36 w-36">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="absolute inset-0 rounded-full border-2 border-glam-rose/40"
            animate={{ scale: [1, 1.35, 1], opacity: [0.5, 0, 0.5] }}
            transition={{
              duration: 2.4,
              repeat: Infinity,
              delay: i * 0.5,
              ease: 'easeInOut',
            }}
          />
        ))}
        <motion.div
          className="absolute inset-6 rounded-full bg-gradient-to-br from-glam-rose/30 to-glam-plum/40 blur-xl"
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            className="h-14 w-14 rounded-2xl bg-zinc-900/90 shadow-lg ring-1 ring-white/10"
            animate={{ rotate: [0, 6, -6, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          />
        </div>
      </div>
      <div className="max-w-sm text-center">
        <motion.p
          className="font-display text-xl font-semibold text-white"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {label}
        </motion.p>
        <p className="mt-2 text-sm text-zinc-400">
          FLUX inpainting and step planning can take 20–60 seconds. Keep this tab open.
        </p>
      </div>
    </div>
  )
}
