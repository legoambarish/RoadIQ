import { useEffect, useRef } from 'react'
import type { BinaryMaskRLE } from '../lib/api'

export function SemanticMaskOverlay({ mask, color }: { mask: BinaryMaskRLE; color: string }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = ref.current
    const [height, width] = mask.size_px
    if (!canvas || mask.encoding !== 'row_major_binary_rle_v1' || !Number.isSafeInteger(width) || !Number.isSafeInteger(height) ||
      width <= 0 || height <= 0 || width * height > 40_000_000 || mask.counts.length > 1_000_000 ||
      mask.counts.some((n) => !Number.isSafeInteger(n) || n < 0) || mask.counts.reduce((a, b) => a + b, 0) !== width * height) return
    const scale = Math.min(1, 1536 / Math.max(width, height))
    canvas.width = Math.max(1, Math.round(width * scale))
    canvas.height = Math.max(1, Math.round(height * scale))
    const context = canvas.getContext('2d')
    if (!context) return
    context.scale(canvas.width / width, canvas.height / height)
    context.fillStyle = color
    let offset = 0
    mask.counts.forEach((count, index) => {
      if (index % 2 && count) {
        let start = offset
        const end = offset + count
        const firstRowEnd = Math.min(end, (Math.floor(start / width) + 1) * width)
        context.fillRect(start % width, Math.floor(start / width), firstRowEnd - start, 1)
        start = firstRowEnd
        const fullRows = Math.floor((end - start) / width)
        if (fullRows) context.fillRect(0, Math.floor(start / width), width, fullRows)
        start += fullRows * width
        if (start < end) context.fillRect(0, Math.floor(start / width), end - start, 1)
      }
      offset += count
    })
  }, [mask, color])
  return <canvas ref={ref} className="semantic-mask-overlay" style={{ aspectRatio: `${mask.size_px[1]} / ${mask.size_px[0]}` }} aria-label={`Experimental predicted ${mask.foreground_label} mask; not ground truth`} />
}
