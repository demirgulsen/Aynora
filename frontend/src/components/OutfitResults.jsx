/**
 * OutfitResults.jsx
 * Shows outfit recommendations progressively as they stream in.
 * Unenriched outfits show skeleton placeholders for images.
 */

export default function OutfitResults({
  outfits, analysis, assistantMessage,
  preview, mode, isLoading,
  onReset, onBack, onNewChat
}) {
  return (
    <div className="results-page">

      {/* Analysis bar — visual mode only */}
      {mode === "visual" && analysis && (
        <div className="analysis-bar">
          <img src={preview} alt="Kıyafet" className="analysis-img" />
          <div className="analysis-content">
            <div className="analysis-tags">
              {[analysis.color, analysis.category, analysis.style, analysis.pattern, analysis.season]
                .filter(Boolean).map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
            </div>
            <p className="analysis-desc">{analysis.description}</p>
          </div>
        </div>
      )}

      {/* Assistant message — chat mode only */}
      {mode === "chat" && assistantMessage && (
        <div className="assistant-message">
          <span className="assistant-icon">◈</span>
          <p>{assistantMessage}</p>
        </div>
      )}

      {/* Outfit cards — progressive */}
      <div className="outfits-grid">
        {outfits.map((outfit, i) => (
          <OutfitCard key={i} outfit={outfit} index={i} />
        ))}
      </div>

      {/* Actions — show when not loading */}
      {!isLoading && outfits.length > 0 && (
        <div className="results-actions">
          <button className="btn-ghost" onClick={onBack}>
            ← {mode === "visual" ? "Filtreleri Değiştir" : "Yeni Soru Sor"}
          </button>
          {mode === "chat" && (
            <button className="btn-ghost" onClick={onNewChat}>
              💬 Devam Et
            </button>
          )}
          <button className="btn-primary" onClick={onReset}>
            ◈ Başa Dön
          </button>
        </div>
      )}
    </div>
  )
}

function OutfitCard({ outfit, index }) {
  const isEnriched = outfit._enriched !== false

  return (
    <div className={`outfit-card ${!isEnriched ? "skeleton-card" : ""}`}>
      <div className="outfit-number">0{index + 1}</div>
      <h3 className="outfit-title">{outfit.title}</h3>
      <p className="outfit-desc">{outfit.description}</p>

      <div className="pieces-list">
        {outfit.pieces?.map((piece, j) => (
          <PieceItem key={j} piece={piece} isEnriched={isEnriched} />
        ))}
      </div>

      <div className="outfit-tip">
        <span className="tip-icon">💡</span>
        <p>{outfit.overall_comment}</p>
      </div>
    </div>
  )
}

function PieceItem({ piece, isEnriched }) {
  const links    = piece.shopping_links || []
  const imageUrl = piece.image_url

  return (
    <div className="piece-item">
      <div className="piece-body">

        {/* Image — skeleton until enriched */}
        <div className="piece-image-wrap">
          {!isEnriched ? (
            <div className="skeleton-img" />
          ) : imageUrl ? (
            <img
              src={imageUrl}
              alt={piece.description}
              className="piece-image"
              onError={e => { e.target.style.display = "none" }}
            />
          ) : (
            <div className="piece-no-img">?</div>
          )}
        </div>

        {/* Info */}
        <div className="piece-info">
          <span className="piece-category">{piece.category}</span>
          <p className="piece-desc">{piece.description}</p>
          <span className="piece-color">● {piece.color}</span>

          {/* Links — skeleton until enriched */}
          {!isEnriched ? (
            <div className="skeleton-links">
              <div className="skeleton-link-item" />
              <div className="skeleton-link-item" />
            </div>
          ) : links.length > 0 ? (
            <div className="piece-links">
              {links.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="piece-link"
                >
                  {link.source} →
                </a>
              ))}
            </div>
          ) : piece.where_to_find ? (
            <span className="piece-where">📍 {piece.where_to_find}</span>
          ) : null}
        </div>
      </div>
    </div>
  )
}