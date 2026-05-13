const CONCEPTS = [
  { value: "casual",            label: "Günlük" },
  { value: "business",          label: "İş" },
  { value: "wedding",           label: "Düğün" },
  { value: "special_invitation",label: "Özel Davet" },
  { value: "sport",             label: "Spor" },
  { value: "date",              label: "Randevu" },
  { value: "night_out",         label: "Gece Çıkışı" },
  { value: "graduation",        label: "Mezuniyet" },
  { value: "home_loungewear",   label: "Ev Kıyafeti" },
  { value: "interview",         label: "Mülakat" },
]

const SIZES = ["XS", "S", "M", "L", "XL", "XXL"]

const COLORS = [
  { value: "no_preference", label: "Fark Etmez" },
  { value: "neutral",       label: "Nötr" },
  { value: "vibrant",       label: "Canlı" },
  { value: "pastel",        label: "Pastel" },
  { value: "dark",          label: "Koyu" },
  { value: "light",         label: "Açık" },
  { value: "monochrome",    label: "Monokrom" },
  { value: "earth_tones",   label: "Toprak" },
  { value: "metallic",      label: "Metalik" },
]

const GENDERS = [
  { value: "female", label: "Kadın" },
  { value: "male",   label: "Erkek" },
  { value: "unisex", label: "Unisex" },
]

const WEATHERS = [
  { value: "sunny", label: "☀️ Güneşli" },
  { value: "hot",   label: "🌡️ Sıcak" },
  { value: "cold",  label: "❄️ Soğuk" },
  { value: "rainy", label: "🌧️ Yağmurlu" },
]

export default function FilterPanel({ filters, onChange, onSubmit, loading }) {
  const set = (key, val) => onChange({ ...filters, [key]: val })

  return (
    <div className="filter-panel">
      <h2 className="filter-title">Tercihlerini Belirle</h2>

      {/* Concept */}
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

      {/* Size */}
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

      {/* Color */}
      <div className="filter-group">
        <label className="filter-label">Renk Tercihi</label>
        <div className="chip-group">
          {COLORS.map(c => (
            <button
              key={c.value}
              className={`chip ${filters.color_preference === c.value ? "chip-active" : ""}`}
              onClick={() => set("color_preference", c.value)}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Gender + Weather */}
      <div className="filter-row">
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
          <label className="filter-label">Hava Durumu</label>
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
      </div>

      {/* Additional notes */}
      <div className="filter-group">
        <label className="filter-label">Ek Not <span className="optional">(opsiyonel)</span></label>
        <textarea
          className="notes-input"
          placeholder="Örn: Vintage tarz olsun, sadece keten parçalar..."
          value={filters.additional_notes}
          onChange={e => set("additional_notes", e.target.value)}
          rows={2}
        />
      </div>

      {/* Submit */}
      <button
        className="btn-primary"
        onClick={onSubmit}
        disabled={loading}
      >
        {loading ? (
          <span className="loading-text">
            <span className="spinner" /> Kombin Hazırlanıyor...
          </span>
        ) : (
          "◈ Kombin Öner"
        )}
      </button>
    </div>
  )
}
