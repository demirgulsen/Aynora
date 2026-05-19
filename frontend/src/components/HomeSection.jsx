/**
 * HomeSection.jsx
 * Tek sayfa — görsel yükleme + metin girişi + inline filtreler
 * Sidebar collapsed başlar, filtreler her zaman görünür
 */

import { useState, useRef, useCallback } from "react"
import FilterPanel from "./FilterPanel"



const SUGGESTIONS = [
  "Hafta sonu brunch için ne giyebilirim?",
  "İş görüşmesi için şık ama rahat bir kombin",
  "Yaz akşamı için hafif ve zarif",
  "Spor sonrası şık görünmek istiyorum",
]

export default function HomeSection({ filters, onFiltersChange, onSubmit }) {
  const [message,     setMessage]     = useState("")
  const [image,       setImage]       = useState(null)   // base64
  const [preview,     setPreview]     = useState(null)   // url
  const [dragging,    setDragging]    = useState(false)
  const [filterOpen, setFilterOpen] = useState(false)
  const fileRef = useRef()
  const textRef = useRef()

  const processFile = useCallback((file) => {
    if (!file || !file.type.startsWith("image/")) return
    const reader = new FileReader()
    reader.onload = (e) => {
      const dataUrl = e.target.result
      setPreview(dataUrl)
      setImage(dataUrl.split(",")[1])
    }
    reader.readAsDataURL(file)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    processFile(e.dataTransfer.files[0])
  }, [processFile])

  const handleSubmit = () => {
    if (!message.trim() && !image) return
    onSubmit({ message, image, filters })
  }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
      <div className="home-page">

      {/* Hero */}
      <div className="home-hero">
        <h1 className="hero-title">
          Stilini Keşfet,{" "}
          <span className="hero-accent">Kombinini</span> Yarat
        </h1>
        <p className="hero-sub">
          Fotoğraf yükle ya da ne giymek istediğini yaz — AI kombini senin için oluştursun
        </p>
      </div>

      <div className="home-input-wrapper">
          {/* Image */}
          <div
            className="home-img-slot"
            onClick={() => fileRef.current.click()}
            title="Görsel Ekle"
          >
            {preview ? (
              <>
                <img src={preview} alt="Yüklenen" className="home-img-thumb" />
                <button
                  className="home-img-remove"
                  onClick={e => { e.stopPropagation(); setImage(null); setPreview(null) }}
                >✕</button>
              </>
            ) : (
              <>
                <span className="home-img-icon">📸</span>
                <span className="home-img-label">Görsel Ekle</span>
              </>
            )}
            <input ref={fileRef} type="file" accept="image/*"
              style={{ display:"none" }} onChange={e => processFile(e.target.files[0])} />
          </div>

          <div className="home-right-col">
              {/* Input Card */}
              <div
                className={`home-input-card ${dragging ? "dragging" : ""}`}
                onDragOver={e => { e.preventDefault(); setDragging(true)  }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
              >
                {/* Top row: image slot + textarea + send */}
                <div className="home-input-top">
                  {/* Textarea */}
                  <textarea
                    ref={textRef}
                    className="home-textarea"
                    placeholder={
                      image
                        ? "Fotoğrafla birlikte kombin tercihin var mı? (opsiyonel)"
                        : "Nasıl bir kombin istersin? Yaz veya fotoğraf ekle..."
                    }
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    onKeyDown={handleKey}
                    rows={3}
                  />

                  {/* Send */}
                  <button
                    className="home-send-btn"
                    onClick={handleSubmit}
                    disabled={!message.trim() && !image}
                    title="Kombin Oluştur"
                  >
                    <span className="home-send-icon">◈</span>
                    <span className="home-send-label">Kombin Oluştur</span>
                  </button>
                </div>
              </div>

              {/* Gönder alt bar */}
              <div className="home-filter-block">
                  {/* Filter Toggle Bar */}
                <div className="home-filter-bar">
                  <div className="home-filter-bar-left">
                    <span className="home-filter-bar-icon">◈</span>
                    <span className="home-filter-bar-title">Tercihler</span>
                    {/* Aktif filtre özetini göster */}
                    <div className="home-filter-pills">
                      <span className="home-filter-pill">Konsept</span>
                      <span className="home-filter-pill">Beden</span>
                      <span className="home-filter-pill">Renk</span>
                      <span className="home-filter-pill">Cinsiyet</span>
                      <span className="home-filter-pill">☀️Hava</span>
                    </div>
                  </div>
                  <button
                    className={`home-filter-toggle-btn ${filterOpen ? "open" : ""}`}
                   onClick={() => setFilterOpen(v => !v)}
                  >
                    <span className="hft-label">{filterOpen ? "Kapat" : "Filtrele"}</span>
                    <span className="hft-arrow">{filterOpen ? "▲" : "▼"}</span>
                  </button>
                </div>

                {/* Collapsible panel */}
                {filterOpen && (
                  <div className="home-filter-panel-wrap">
                    <FilterPanel
                      filters={filters}
                      onChange={onFiltersChange}
                      onSubmit={handleSubmit}
                      loading={false}
                    />
                  </div>
                )}
              </div>

              {/* Suggestions */}
              <div className="home-suggestions">
              <span className="home-sug-label">Popüler Başlangıçlar</span>
              <div className="home-sug-list">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="f-pill-sug"
                    onClick={() => { setMessage(s); textRef.current?.focus() }}>
                    <span className="f-pill-sug-icon">◈</span>{s}
                  </button>
                ))}
              </div>
            </div>

          </div>
      </div>
    </div>
  )
}