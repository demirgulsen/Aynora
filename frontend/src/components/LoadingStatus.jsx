/**
 * LoadingStatus.jsx — Pipeline progress indicator
 * Shows current stage with animated progress bar and stage steps.
 */

const STAGES = [
  { key: "analyzing",  icon: "◎", label: "Analiz"    },
  { key: "searching",  icon: "◈", label: "Arama"     },
  { key: "generating", icon: "✦", label: "Oluşturma" },
  { key: "enriching",  icon: "◉", label: "Görseller" },
]

export default function LoadingStatus({ stage, message, enrichedCount, totalCount }) {
  const currentIndex = STAGES.findIndex(s => s.key === stage)
  const progress = totalCount > 0 && stage === "enriching"
    ? Math.round((enrichedCount / totalCount) * 100)
    : currentIndex >= 0 ? Math.round(((currentIndex) / STAGES.length) * 100) : 0

  return (
    <div className="loading-status">
      {/* Stage steps */}
      <div className="stage-track">
        {STAGES.map((s, i) => {
          const isActive    = s.key === stage
          const isCompleted = currentIndex > i
          return (
            <div key={s.key} className={`stage-step ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}>
              <div className="stage-dot">
                {isCompleted
                  ? <span className="check">✓</span>
                  : isActive
                  ? <span className="pulse-dot" />
                  : <span className="stage-icon">{s.icon}</span>
                }
              </div>
              <span className="stage-label">{s.label}</span>
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Message */}
      {message && (
        <div className="stage-message">
          <span className="spinner-sm" />
          <span>{message}</span>
          {stage === "enriching" && totalCount > 0 && (
            <span className="enrich-badge">{enrichedCount}/{totalCount}</span>
          )}
        </div>
      )}
    </div>
  )
}