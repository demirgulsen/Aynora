export default function LandingSection({ onSelect }) {
  return (
    <div className="landing-page">
      <div className="landing-hero">
        <h1 className="hero-title">
          Stilini Keşfet,<br />
          <span className="hero-accent">Kombinini Yarat</span>
        </h1>
        <p className="hero-sub">
          Yapay zeka destekli kombin asistanınız.<br />
          Kıyafet yükle veya sadece yaz — sana özel kombinler hazırlayalım.
        </p>
      </div>

      <div className="mode-cards">
        {/* Görsel Mod */}
        <div className="mode-card" onClick={() => onSelect("visual")}>
          <div className="mode-icon">📸</div>
          <h2 className="mode-title">Kıyafet Yükle</h2>
          <p className="mode-desc">
            Elindeki bir kıyafetin fotoğrafını yükle,
            yapay zeka analiz etsin ve tamamlayıcı
            kombin önerileri sunsun.
          </p>
          <div className="mode-cta">Fotoğraf Yükle →</div>
        </div>

        {/* Chat Mod */}
        <div className="mode-card" onClick={() => onSelect("chat")}>
          <div className="mode-icon">💬</div>
          <h2 className="mode-title">Kombin İste</h2>
          <p className="mode-desc">
            Fotoğraf yüklemene gerek yok. Sadece ne
            istediğini yaz — "düğün için şık kombin"
            gibi — gerisini biz halledelim.
          </p>
          <div className="mode-cta">Yazmaya Başla →</div>
        </div>
      </div>

      <div className="landing-features">
        <div className="feature">
          <span className="feature-icon">◎</span>
          <span>AI destekli görsel analiz</span>
        </div>
        <div className="feature">
          <span className="feature-icon">◎</span>
          <span>Gerçek ürün görselleri ve linkleri</span>
        </div>
        <div className="feature">
          <span className="feature-icon">◎</span>
          <span>Konsept ve beden bazlı öneriler</span>
        </div>
      </div>
    </div>
  )
}