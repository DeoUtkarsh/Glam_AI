import { motion } from 'framer-motion'
import type { GenerateMakeupResponse, Region } from '../api/types'
import { pngDataUrl } from '../api/client'

const regionStyle: Record<Region, string> = {
  skin: 'bg-rose-500/20 text-rose-200 ring-rose-500/30',
  lips: 'bg-red-500/20 text-red-200 ring-red-500/30',
  eyes: 'bg-violet-500/20 text-violet-200 ring-violet-500/30',
  brows: 'bg-amber-500/20 text-amber-200 ring-amber-500/30',
}

export function ResultsTimeline({ data }: { data: GenerateMakeupResponse }) {
  const finalSrc = data.final_image ? pngDataUrl(data.final_image) : null

  return (
    <div className="mx-auto max-w-2xl space-y-12 pb-24">
      <section>
        <p className="text-xs font-medium uppercase tracking-widest text-glam-rose">Phase 1</p>
        <h2 className="font-display mt-1 text-2xl font-semibold text-white">Final look</h2>
        <p className="mt-1 text-sm text-zinc-400">
          {data.style_name} — full FLUX result on your masked face region.
        </p>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/40 shadow-2xl"
        >
          {finalSrc ? (
            <img
              src={finalSrc}
              alt={`${data.style_name} makeup result`}
              className="aspect-[3/4] w-full object-cover sm:aspect-[4/5]"
            />
          ) : (
            <div className="flex aspect-[3/4] items-center justify-center text-zinc-500">
              No image returned
            </div>
          )}
        </motion.div>
      </section>

      <section>
        <p className="text-xs font-medium uppercase tracking-widest text-glam-plum">Phase 2</p>
        <h2 className="font-display mt-1 text-2xl font-semibold text-white">Tutorial steps</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Masked reveal: each step layers makeup from the final render onto your original photo.
        </p>

        <div className="relative mt-8 space-y-10 pl-2">
          <div className="absolute left-[19px] top-4 bottom-4 w-px bg-gradient-to-b from-glam-rose/50 via-glam-plum/40 to-transparent" />

          {data.steps.map((step, idx) => {
            const src = step.image ? pngDataUrl(step.image) : null
            return (
              <motion.article
                key={step.step_num}
                initial={{ opacity: 0, x: -8 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ delay: idx * 0.05 }}
                className="relative flex gap-6"
              >
                <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-sm font-bold text-white ring-2 ring-glam-rose/40">
                  {step.step_num}
                </div>
                <div className="min-w-0 flex-1 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-display text-lg font-semibold text-white">{step.name}</h3>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ring-1 ${regionStyle[step.region]}`}
                    >
                      {step.region}
                    </span>
                  </div>
                  <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
                    {src ? (
                      <img
                        src={src}
                        alt={`Step ${step.step_num}: ${step.name}`}
                        className="aspect-[3/4] w-full object-cover sm:aspect-[4/5]"
                      />
                    ) : (
                      <div className="flex aspect-video items-center justify-center text-sm text-zinc-500">
                        No preview
                      </div>
                    )}
                  </div>
                </div>
              </motion.article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
