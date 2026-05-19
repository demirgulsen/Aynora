/**
 * TryOnSection.jsx
 * Sanal Kabin — sepetteki ürünleri gösterir,
 * ileride gerçek try-on entegrasyonu buraya gelecek
 */

export default function TryOnSection({ cartItems, onOpenCart, onRemoveFromCart }) {
  return (
    <div className="tryon-page">

      {/* Hero */}
      <div className="tryon-hero">
        <div className="tryon-badge">Yakında · Beta</div>
        <h1 className="hero-title">
          Sanal <span className="hero-accent">Kabin</span>
        </h1>
        <p className="hero-sub" style={{ maxWidth: 520 }}>
          Yapay zeka destekli sanal deneme kabinimiz yakında burada olacak.
          Seçtiğin kombinleri üzerinde görselleştir, satın almadan önce nasıl
          durduğunu gör.
        </p>
      </div>

      {/* Coming soon visual */}
      <div className="tryon-canvas">
        <div className="tryon-mannequin">
          <div className="tryon-mannequin-icon">◑</div>
          <p className="tryon-mannequin-label">3D Deneme Alanı</p>
          <p className="tryon-mannequin-sub">Geliştirme aşamasında</p>
        </div>

        <div className="tryon-features">
          {[
            { icon: "◈", title: "Sanal Modelde Gör",      desc: "Seçtiğin parçaları gerçekçi bir model üzerinde görselleştir" },
            { icon: "◉", title: "Fotoğrafınla Dene",       desc: "Kendi fotoğrafını yükle, kombini üzerinde görselleştir" },
            { icon: "◈", title: "AI Beden Analizi",     desc: "Fotoğrafından beden ölçülerini çıkar" },
            { icon: "✦", title: "Kombin Kaydet",         desc: "Beğendiğin kombinleri arşivle"        },
          ].map((f) => (
            <div key={f.title} className="tryon-feature-item">
              <span className="tryon-feature-icon">{f.icon}</span>
              <div>
                <div className="tryon-feature-title">{f.title}</div>
                <div className="tryon-feature-desc">{f.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sepet */}
      <div className="tryon-cart-section">
        <div className="tryon-cart-header">
          <div>
            <h2 className="tryon-cart-title">Seçilen Parçalar</h2>
            <p className="tryon-cart-sub">
              {cartItems.length === 0
                ? "Kombin oluşturarak buraya parça ekleyebilirsin"
                : `${cartItems.length} parça sanal kabine hazır`}
            </p>
          </div>
          {cartItems.length > 0 && (
            <button className="btn-ghost" onClick={onOpenCart}>
              Sepeti Yönet
            </button>
          )}
        </div>

        {cartItems.length === 0 ? (
          <div className="tryon-cart-empty">
            <div className="tryon-empty-icon">◈</div>
            <p>Henüz parça eklemedin.</p>
            <p className="tryon-empty-sub">
              Kombin Oluştur bölümünden beğendiğin ürünleri sepete ekle,
              burada sanal kabinde dene.
            </p>
          </div>
        ) : (
          <div className="tryon-cart-grid">
            {cartItems.map((piece, i) => (
              <div key={i} className="tryon-cart-card">
                <div className="tryon-cart-img-wrap">
                  {piece.image_url ? (
                    <img
                      src={piece.image_url}
                      alt={piece.description}
                      className="tryon-cart-img"
                      onError={e => { e.target.style.display = "none" }}
                    />
                  ) : (
                    <div className="piece-no-img">?</div>
                  )}
                  <button
                    className="tryon-cart-remove"
                    onClick={() => onRemoveFromCart(i)}
                    title="Kaldır"
                  >✕</button>
                </div>
                <div className="tryon-cart-info">
                  <span className="piece-category">{piece.category}</span>
                  <p className="tryon-cart-desc">{piece.description}</p>
                  <span className="piece-color">● {piece.color}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}