/**
 * App.jsx — Aynora v3
 * HomeSection tek giriş noktası; sidebar collapsed başlar
 */

import { useState } from "react"
import { useStreamingRecommend } from "./hooks/useStreamingRecommend"
import { useDarkMode }           from "./hooks/useDarkMode"
import Sidebar      from "./components/Sidebar"
import HomeSection  from "./components/HomeSection"
import FilterPanel  from "./components/FilterPanel"
import OutfitResults from "./components/OutfitResults"
import TryOnSection from "./components/TryOnSection"
import "./index.css"

export default function App() {
  const { theme, toggleTheme } = useDarkMode()

  // ── Filters (shared, always visible in HomeSection) ───────
  const [filters, setFilters] = useState({
    concept:          "casual",
    size:             "M",
    color_preference: "no_preference",
    gender:           "female",
    language:         "tr",
    weather:          "sunny",
    additional_notes: "",
  })

  // ── Steps: "home" | "result" | "tryon" ────────────────────
  const [step,  setStep]  = useState("home")
  const [mode,  setMode]  = useState(null)   // "visual" | "chat"
  const [image, setImage] = useState(null)   // base64, for load-more

  // ── Sidebar ───────────────────────────────────────────────
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)  // collapsed başlar

  // ── Cart ──────────────────────────────────────────────────
  const [cartItems, setCartItems] = useState([])
  const [cartOpen,  setCartOpen]  = useState(false)

  // ── Streaming ─────────────────────────────────────────────
  const {
    stage, analysis, assistantMessage,
    outfits, enrichedCount,
    error, loadingMore, isLoading,
    recommendVisual, recommendChat,
    loadMore, reset: resetStream,
  } = useStreamingRecommend()

  // ── Handlers ──────────────────────────────────────────────

  // HomeSection submit — message ve/veya image gelir
  const handleHomeSubmit = async ({ message, image: img, filters: mergedFilters }) => {
    resetStream()
    const merged = { ...filters, ...mergedFilters }
    setFilters(merged)

    if (img) {
      // Görsel varsa → visual mod
      setMode("visual")
      setImage(img)
      setStep("result")
      await recommendVisual(img, merged)
    } else {
      // Sadece metin → chat mod
      setMode("chat")
      setImage(null)
      setStep("result")
      await recommendChat(message, merged, [])
    }
  }

  const handleLoadMore = () => {
    if (mode === "visual") {
      loadMore("/outfit/recommend/stream", { image, ...filters })
    } else {
      loadMore("/outfit/chat-recommend/stream", { message: "", ...filters, chat_history: [] })
    }
  }

  const handleReset = () => {
    setMode(null)
    setImage(null)
    resetStream()
    setStep("home")
  }

  const handleBack = () => {
    resetStream()
    setStep("home")
  }

  const handleNavigate = (targetStep) => {
    resetStream()
    if (targetStep === "tryon") {
      setStep("tryon")
    } else if (targetStep === "workspace" || targetStep === "home") {
      setStep("home")
    } else {
      setStep(targetStep)
    }
  }

  // ── Progress ───────────────────────────────────────────────
  const progressWidth =
    stage === "analyzing"  ? "20%" :
    stage === "searching"  ? "42%" :
    stage === "generating" ? "65%" :
    stage === "enriching" && outfits.length > 0
      ? `${68 + Math.round((enrichedCount / outfits.length) * 30)}%`
    : isLoading ? "10%" : "0%"

  // ── Breadcrumb ─────────────────────────────────────────────
  const breadcrumb = {
    home:   "Kombin Oluştur",
    result: mode === "visual" ? "Görsel Analiz › Sonuçlar" : "Stil Asistanı › Sonuçlar",
    tryon:  "Hadi Dene! › Sanal Kabin",
  }[step] || ""

  // ── Render ────────────────────────────────────────────────
  return (
    <div className={`app ${sidebarCollapsed ? "sidebar-is-collapsed" : ""}`}>

      {/* Sidebar */}
      <Sidebar
        currentStep={step}
        onNavigate={handleNavigate}
        onReset={handleReset}
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(v => !v)}
      />

      {/* Sidebar toggle — sidebar dışında, üstte sabit */}
      <button
        className="sidebar-toggle-floating"
        onClick={() => setSidebarCollapsed(v => !v)}
        title={sidebarCollapsed ? "Menüyü Aç" : "Menüyü Gizle"}
      >
        {sidebarCollapsed ? "›" : "‹"}
      </button>

      {/* Main */}
      <div className="main-content">

        {/* Top progress bar */}
        <div className="top-bar">
          <div className="top-bar-fill" style={{ width: progressWidth }} />
        </div>

        {/* Header */}
        <header className="header">
          <div className="header-breadcrumb">
            <span>{breadcrumb}</span>
          </div>
          <div className="header-actions">
            {/* Sepet */}
            <button className="cart-btn" onClick={() => setCartOpen(true)}>
              🛍️ Kombin Sepetim
              {cartItems.length > 0 && (
                <span className="cart-badge">{cartItems.length}</span>
              )}
            </button>

            {/* Tema */}
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === "dark" ? "Açık Tema" : "Koyu Tema"}
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>

            {/* Geri — sadece result'ta */}
            {step !== "home" && (
              <button className="btn-ghost" onClick={handleReset}>
                ← Ana Sayfa
              </button>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="main">

          {/* ── Home ── */}
          {step === "home" && (
            <HomeSection
              filters={filters}
              onFiltersChange={setFilters}
              onSubmit={handleHomeSubmit}
            />
          )}

          {/* ── Result ── */}
          {step === "result" && (
            <div className="result-stage">

              {/* Pipeline card */}
              {(isLoading || analysis) && (
                <div className="pipeline-card">
                  {analysis && (
                    <div className="pipeline-analysis">
                      {mode === "visual" && image && (
                        <img
                          src={`data:image/jpeg;base64,${image}`}
                          alt="Kıyafet"
                          className="pipeline-thumb"
                        />
                      )}
                      <div className="pipeline-meta">
                        <div className="pipeline-tags">
                          {[analysis.color, analysis.category, analysis.style, analysis.pattern]
                            .filter(Boolean)
                            .map((t, i) => (
                              <span key={i} className="pipeline-tag">{t}</span>
                            ))}
                        </div>
                        <p className="pipeline-desc">{analysis.description}</p>
                      </div>
                    </div>
                  )}

                  {analysis && isLoading && <div className="pipeline-divider" />}

                  {isLoading && (
                    <div className="pipeline-steps">
                      {[
                        { key: "analyzing",  label: "Kıyafet analiz ediliyor"      },
                        { key: "searching",  label: "Benzer kombinler aranıyor"     },
                        { key: "generating", label: "Kombin önerileri hazırlanıyor" },
                        { key: "enriching",  label: "Ürün görselleri yükleniyor"    },
                      ].map((s) => {
                        const stageList = ["analyzing","searching","generating","enriching"]
                        const cur = stageList.indexOf(stage)
                        const idx = stageList.indexOf(s.key)
                        if (idx > cur) return null
                        const isActive    = s.key === stage
                        const isCompleted = idx < cur
                        return (
                          <div
                            key={s.key}
                            className={`pipeline-step ${isActive ? "ps-active" : ""} ${isCompleted ? "ps-done" : ""}`}
                          >
                            <span className="ps-icon">
                              {isCompleted ? "✓" : isActive ? <span className="ps-spinner" /> : "○"}
                            </span>
                            <span className="ps-label">
                              {s.label}
                              {isActive && s.key === "enriching" && outfits.length > 0 && (
                                <span className="ps-count"> {enrichedCount}/{outfits.length}</span>
                              )}
                            </span>
                          </div>
                        )
                      })}
                      <div className="ps-bar-track">
                        <div className="ps-bar-fill" style={{ width: progressWidth }} />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Assistant message */}
              {mode === "chat" && assistantMessage && !isLoading && (
                <div className="assistant-message">
                  <span className="assistant-icon">◈</span>
                  <p>{assistantMessage}</p>
                </div>
              )}

              {error && <div className="error-msg">⚠ {error}</div>}

              {outfits.length > 0 && (
                <OutfitResults
                  outfits={outfits}
                  mode={mode}
                  isLoading={isLoading}
                  loadingMore={loadingMore}
                  onReset={handleReset}
                  onBack={handleBack}
                  onNewChat={handleReset}
                  onLoadMore={handleLoadMore}
                  cartItems={cartItems}
                  onAddToCart={(piece) => setCartItems(prev => [...prev, piece])}
                />
              )}
            </div>
          )}

          {/* ── Try-On ── */}
          {step === "tryon" && (
            <TryOnSection
              cartItems={cartItems}
              onOpenCart={() => setCartOpen(true)}
              onRemoveFromCart={(i) => setCartItems(prev => prev.filter((_, idx) => idx !== i))}
            />
          )}

        </main>

        <footer className="footer">
          © 2025 Aynora · Yapay Zeka Destekli Moda
        </footer>
      </div>

      {/* ── Cart Modal ── */}
      {cartOpen && (
        <div className="modal-backdrop" onClick={() => setCartOpen(false)}>
          <div className="modal cart-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="modal-category">Kombin Sepetim</div>
                <div className="modal-title">Seçilen Parçalar</div>
              </div>
              <button className="modal-close" onClick={() => setCartOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              {cartItems.length === 0 ? (
                <div className="modal-empty">
                  <div style={{ fontSize: "2rem", marginBottom: "0.75rem", opacity: 0.3 }}>◈</div>
                  <p>Henüz sepetine ürün eklemedin.</p>
                </div>
              ) : (
                <div className="cart-items-list">
                  {cartItems.map((piece, i) => (
                    <div key={i} className="cart-item">
                      <div className="cart-item-img-wrap">
                        {piece.image_url ? (
                          <img src={piece.image_url} alt={piece.description} className="cart-item-img"
                            onError={e => e.target.style.display="none"} />
                        ) : (
                          <div className="piece-no-img">?</div>
                        )}
                      </div>
                      <div className="cart-item-info">
                        <span className="piece-category">{piece.category}</span>
                        <p className="piece-desc">{piece.description}</p>
                        <span className="piece-color">● {piece.color}</span>
                        {piece.shopping_links?.length > 0 && (
                          <div className="piece-links" style={{ marginTop: "0.4rem" }}>
                            {piece.shopping_links.map((link, j) => (
                              <a key={j} href={link.url} target="_blank" rel="noopener noreferrer" className="piece-link">
                                {link.source} →
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                      <button
                        className="cart-item-remove"
                        onClick={() => setCartItems(prev => prev.filter((_, idx) => idx !== i))}
                        title="Kaldır"
                      >✕</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {cartItems.length > 0 && (
              <div className="cart-footer">
                <span className="cart-count">{cartItems.length} parça seçildi</span>
                <button className="btn-ghost" onClick={() => setCartItems([])}>Sepeti Temizle</button>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  )
}