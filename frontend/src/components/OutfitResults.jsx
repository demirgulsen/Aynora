const CONCEPT_LABELS = {
  casual: "Günlük", business: "İş", wedding: "Düğün",
  special_invitation: "Özel Davet", sport: "Spor", date: "Randevu",
  night_out: "Gece Çıkışı", graduation: "Mezuniyet",
  home_loungewear: "Ev Kıyafeti", interview: "Mülakat"
}

export default function OutfitResults({ result, preview, onReset, onBack }) {
  const { analysis, recommendations } = result
  const outfits = recommendations?.outfits || []

  return (
    <div className="results-page">

      {/* Analysis bar */}
      <div className="analysis-bar">
        <img src={preview} alt="Kıyafet" className="analysis-img" />
        <div className="analysis-tags">
          <span className="tag">{analysis.color}</span>
          <span className="tag">{analysis.category}</span>
          <span className="tag">{analysis.style}</span>
          <span className="tag">{analysis.pattern}</span>
          {analysis.season && <span className="tag">{analysis.season}</span>}
        </div>
        <p className="analysis-desc">{analysis.description}</p>
      </div>

      {/* Outfits */}
      <div className="outfits-grid">
        {outfits.map((outfit, i) => (
          <div key={i} className="outfit-card">
            <div className="outfit-number">0{i + 1}</div>
            <h3 className="outfit-title">{outfit.title}</h3>
            <p className="outfit-desc">{outfit.description}</p>

            <div className="pieces-list">
              {outfit.pieces.map((piece, j) => (
                <div key={j} className="piece-item">
                  <div className="piece-header">
                    <span className="piece-category">{piece.category}</span>
                    <span
                      className="piece-color-dot"
                      title={piece.color}
                    />
                  </div>
                  <p className="piece-desc">{piece.description}</p>
                  <div className="piece-footer">
                    <span className="piece-color-label">{piece.color}</span>
                    <span className="piece-where">📍 {piece.where_to_find}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="outfit-tip">
              <span className="tip-icon">💡</span>
              <p>{outfit.overall_comment}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="results-actions">
        <button className="btn-ghost" onClick={onBack}>
          ← Filtreleri Değiştir
        </button>
        <button className="btn-primary" onClick={onReset}>
          ◈ Yeni Kıyafet Yükle
        </button>
      </div>
    </div>
  )
}
