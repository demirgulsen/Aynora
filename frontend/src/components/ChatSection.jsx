import { useRef, useEffect } from "react"

const CONCEPTS = [
  { value: "casual",             label: "Günlük" },
  { value: "business",           label: "İş" },
  { value: "wedding",            label: "Düğün" },
  { value: "special_invitation", label: "Özel Davet" },
  { value: "sport",              label: "Spor" },
  { value: "date",               label: "Randevu" },
  { value: "night_out",          label: "Gece Çıkışı" },
  { value: "graduation",         label: "Mezuniyet" },
  { value: "home_loungewear",    label: "Ev Kıyafeti" },
  { value: "interview",          label: "Mülakat" },
]

const SIZES    = ["XS", "S", "M", "L", "XL", "XXL"]
const GENDERS  = [{ value: "female", label: "Kadın" }, { value: "male", label: "Erkek" }, { value: "unisex", label: "Unisex" }]
const WEATHERS = [{ value: "sunny", label: "☀️" }, { value: "hot", label: "🌡️" }, { value: "cold", label: "❄️" }, { value: "rainy", label: "🌧️" }]

const SUGGESTIONS = [
  "Yarın iş toplantım var, profesyonel ama sıkıcı olmayan bir kombin öner",
  "Hafta sonu brunch için rahat ve şık bir kombin istiyorum",
  "Düğüne gidiyorum, davetli olarak ne giysem?",
  "Spor salonuna gidip sonra kahveye çıkacağım, ne önerirsin?",
]

export default function ChatSection({
  filters, onFiltersChange,
  message, onMessageChange,
  onSubmit, chatHistory,
  loading, error, onBack
}) {
  const textareaRef = useRef()
  const historyRef  = useRef()

  const set = (key, val) => onFiltersChange({ ...filters, [key]: val })

  // Auto-scroll chat history
  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight
    }
  }, [chatHistory])

  const handleKeyDown = (e) => {
    // Submit on Enter (not Shift+Enter)
    if (e.key === "Enter" && !e.shiftKey && !loading) {
      e.preventDefault()
      if (message.trim()) onSubmit(message)
    }
  }

  return (
    <div className="chat-page">

      {/* Back */}
      <button className="btn-ghost back-btn" onClick={onBack}>
        ← Geri
      </button>

      <div className="chat-layout">

        {/* Left — Filters */}
        <aside className="chat-filters">
          <h3 className="filter-title">Tercihler</h3>

          <div className="filter-group">
            <label className="filter-label">Konsept</label>
            <div className="chip-group">
              {CONCEPTS.map(c => (
                <button
                  key={c.value}
                  className={`chip ${filters.concept === c.value ? "chip-active" : ""}`}
                  onClick={() => set("concept", c.value)}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <label className="filter-label">Beden</label>
            <div className="chip-group">
              {SIZES.map(s => (
                <button
                  key={s}
                  className={`chip ${filters.size === s ? "chip-active" : ""}`}
                  onClick={() => set("size", s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <label className="filter-label">Cinsiyet</label>
            <div className="chip-group">
              {GENDERS.map(g => (
                <button
                  key={g.value}
                  className={`chip ${filters.gender === g.value ? "chip-active" : ""}`}
                  onClick={() => set("gender", g.value)}
                >
                  {g.label}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <label className="filter-label">Hava</label>
            <div className="chip-group">
              {WEATHERS.map(w => (
                <button
                  key={w.value}
                  className={`chip ${filters.weather === w.value ? "chip-active" : ""}`}
                  onClick={() => set("weather", w.value)}
                >
                  {w.label}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Right — Chat */}
        <div className="chat-main">

          {/* Chat history */}
          {chatHistory.length > 0 && (
            <div className="chat-history" ref={historyRef}>
              {chatHistory.map((msg, i) => (
                <div key={i} className={`chat-bubble ${msg.role}`}>
                  <p>{msg.content}</p>
                </div>
              ))}
              {loading && (
                <div className="chat-bubble assistant">
                  <span className="typing-dots">
                    <span /><span /><span />
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Suggestions — only when no history */}
          {chatHistory.length === 0 && (
            <div className="chat-suggestions">
              <p className="suggestions-label">Örnek istekler:</p>
              <div className="suggestions-list">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    className="suggestion-chip"
                    onClick={() => onMessageChange(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="chat-input-area">
            <textarea
              ref={textareaRef}
              className="chat-input"
              placeholder="Kombin isteğini yaz... (örn: yarın düğüne gidiyorum, ne giyeyim?)"
              value={message}
              onChange={e => onMessageChange(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              disabled={loading}
            />
            <button
              className="chat-send-btn"
              onClick={() => message.trim() && onSubmit(message)}
              disabled={loading || !message.trim()}
            >
              {loading ? <span className="spinner" /> : "◈"}
            </button>
          </div>

          {error && <div className="error-msg">⚠ {error}</div>}

          <p className="chat-hint">Enter ile gönder · Shift+Enter ile yeni satır</p>
        </div>
      </div>
    </div>
  )
}