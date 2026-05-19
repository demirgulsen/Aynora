/**
 * OutfitResults.jsx
 * Kombin kartları + Stil DNA beğen/beğenme butonları
 */

import { useState } from "react"
import ProductModal from "./ProductModal"

const API_BASE = ""

export default function OutfitResults({
  outfits, mode, isLoading, loadingMore,
  onReset, onBack, onNewChat, onLoadMore, onAddToCart
}) {
  return (
    <div className="results-page">
      <div className="outfits-grid">
        {outfits.map((outfit, i) => (
          <OutfitCard key={`${outfit.title}-${i}`} outfit={outfit} index={i} onAddToCart={onAddToCart} />
        ))}
      </div>

      {!isLoading && outfits.length > 0 && (
        <div className="load-more-section">
          <button
            className="btn-load-more"
            onClick={onLoadMore}
            disabled={loadingMore}
          >
            {loadingMore
              ? <><span className="spinner-sm-dark" /> Yükleniyor...</>
              : <>◈ Daha Fazla Kombin</>
            }
          </button>
        </div>
      )}

      {!isLoading && outfits.length > 0 && (
        <div className="results-actions">
          <button className="btn-ghost" onClick={onBack}>
            ← {mode === "visual" ? "Filtreleri Değiştir" : "Yeni Soru Sor"}
          </button>
          {mode === "chat" && (
            <button className="btn-ghost" onClick={onNewChat}>◎ Devam Et</button>
          )}
          <button className="btn-primary" onClick={onReset}>◈ Başa Dön</button>
        </div>
      )}
    </div>
  )
}

// ── Outfit Card ────────────────────────────────────────────
function OutfitCard({ outfit, index, onAddToCart  }) {
  const [dna, setDna] = useState(null) // "liked" | "disliked" | null
  const isEnriched = outfit._enriched !== false

  const handleDna = async (action) => {
    if (dna === action) {
      setDna(null)
      return
    }
    setDna(action)

    // Stil DNA backend'e gönder (endpoint sonradan eklenecek)
    try {
      await fetch(`${API_BASE}/outfit/dna-feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          outfit_title: outfit.title,
          action,        // "liked" | "disliked"
          pieces: outfit.pieces?.map(p => p.description) || [],
        }),
      })
    } catch {
      // Sessizce geç — backend henüz hazır olmayabilir
    }
  }

  return (
    <div className={`outfit-card ${!isEnriched ? "skeleton-card" : "card-appear"}`}>
      <div className="outfit-number">0{index + 1}</div>
      <h3 className="outfit-title">{outfit.title}</h3>
      <p className="outfit-desc">{outfit.description}</p>

      <div className="pieces-list">
        {outfit.pieces?.map((piece, j) => (
          <PieceItem key={j} piece={piece} isEnriched={isEnriched} onAddToCart={onAddToCart} />
        ))}
      </div>

      {outfit.overall_comment && (
        <div className="outfit-tip">
          <span className="tip-icon">◎</span>
          <p>{outfit.overall_comment}</p>
        </div>
      )}

      {/* Stil DNA */}
      <div className="dna-actions">
        <button
          className={`dna-btn like ${dna === "liked" ? "liked" : ""}`}
          onClick={() => handleDna("liked")}
          title="Bu kombini beğendim"
        >
          {dna === "liked" ? "♥" : "♡"} Beğendim
        </button>
        <button
          className={`dna-btn dislike ${dna === "disliked" ? "disliked" : ""}`}
          onClick={() => handleDna("disliked")}
          title="Bu kombin bana göre değil"
        >
          {dna === "disliked" ? "✕" : "○"} Beğenmedim
        </button>
      </div>
    </div>
  )
}

// ── Piece Item ─────────────────────────────────────────────
function PieceItem({ piece, isEnriched, onAddToCart }) {
  const [added, setAdded] = useState(false)
  const handleAddToCart = () => {
    onAddToCart(piece)
    setAdded(true)
    setTimeout(() => setAdded(false), 1800)
  }
  const [modalOpen, setModalOpen] = useState(false)
  const links    = piece.shopping_links || []
  const imageUrl = piece.image_url

  return (
    <div className="piece-item">
      <div className="piece-body" style={{ alignItems: 'flex-start' }}>
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

        <div className="piece-info">
          <span className="piece-category">{piece.category}</span>
          <p className="piece-desc">{piece.description}</p>
          <span className="piece-color">● {piece.color}</span>

          {!isEnriched ? (
            <div className="skeleton-links">
              <div className="skeleton-link-item" />
              <div className="skeleton-link-item" />
            </div>
          ) : (
            <div className="piece-actions">
              {links.length > 0 && (
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
              )}
              {links.length === 0 && piece.where_to_find && (
                <span className="piece-where">◎ {piece.where_to_find}</span>
              )}
              <div className="piece-btn-row">
                  <button
                    className={`btn-add-cart ${added ? "added" : ""}`}
                    onClick={handleAddToCart}
                    disabled={added}
                  >
                    {added ? "✓ Eklendi" : "🛍️ Sepete Ekle"}
                  </button>
                  <button className="btn-find-more" onClick={() => setModalOpen(true)}>
                   🔍 Daha Fazla Bul
                  </button>
              </div>

            </div>
          )}
        </div>
      </div>

      {modalOpen && (
        <ProductModal piece={piece} onClose={() => setModalOpen(false)} />
      )}
    </div>
  )
}