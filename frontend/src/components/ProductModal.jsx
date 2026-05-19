/**
 * ProductModal.jsx
 * Renders via React Portal directly into document.body
 * to avoid overflow:hidden clipping issues.
 */

import { useState, useEffect } from "react"
import { createPortal } from "react-dom"

const API_BASE = "http://127.0.0.1:8003"

export default function ProductModal({ piece, onClose }) {
  const [products, setProducts] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)

  // Prevent body scroll when modal open
  useEffect(() => {
    document.body.style.overflow = "hidden"
    return () => { document.body.style.overflow = "" }
  }, [])

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const params = new URLSearchParams({
          query:       piece.description || "",
          color:       piece.color       || "",
          num_results: 10,
        })
        const res  = await fetch(`${API_BASE}/outfit/search-piece?${params}`)
        const data = await res.json()
        setProducts(data.results || [])
      } catch {
        setError("Ürünler yüklenemedi.")
      } finally {
        setLoading(false)
      }
    }
    fetchProducts()
  }, [piece])

  const modal = (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">

        <div className="modal-header">
          <div>
            <span className="modal-category">{piece.category}</span>
            <h2 className="modal-title">{piece.description}</h2>
            <span className="modal-color">● {piece.color}</span>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="modal-loading">
              <span className="spinner-gold" />
              <p>Ürünler aranıyor...</p>
            </div>
          )}

          {error && <p className="modal-error">{error}</p>}

          {!loading && !error && products.length === 0 && (
            <p className="modal-empty">Ürün bulunamadı.</p>
          )}

          {!loading && products.length > 0 && (
            <div className="modal-products">
              {products.map((product, i) => (
                <a
                  key={i}
                  href={product.page_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="product-card"
                >
                  <div className="product-image-wrap">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt={product.title}
                        className="product-image"
                        onError={e => { e.target.style.display = "none" }}
                      />
                    ) : (
                      <div className="product-no-img">?</div>
                    )}
                  </div>
                  <div className="product-info">
                    <p className="product-title">{product.title}</p>
                    <span className="product-source">{product.source} →</span>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  return createPortal(modal, document.body)
}