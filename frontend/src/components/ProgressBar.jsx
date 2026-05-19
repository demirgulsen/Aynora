/**
 * ProgressBar.jsx — Thin top progress bar (Perplexity-style)
 * Shows pipeline progress as a gold line under the header.
 */

const STAGE_PROGRESS = {
  analyzing:  15,
  searching:  35,
  generating: 60,
  enriching:  80,
}

export default function ProgressBar({ stage, enrichedCount, totalCount }) {
  if (!stage) return null

  let progress = STAGE_PROGRESS[stage] || 0

  // Enriching stage — fill proportionally
  if (stage === "enriching" && totalCount > 0) {
    progress = 80 + Math.round((enrichedCount / totalCount) * 18)
  }

  return (
    <div className="progress-bar-outer">
      <div
        className="progress-bar-inner"
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}
