import { useState } from "react"
import UploadSection from "./components/UploadSection"
import FilterPanel from "./components/FilterPanel"
import OutfitResults from "./components/OutfitResults"
import "./index.css"

export default function App() {
  const [image, setImage] = useState(null)       // base64
  const [preview, setPreview] = useState(null)   // object URL
  const [filters, setFilters] = useState({
    concept: "casual",
    size: "M",
    color_preference: "no_preference",
    gender: "female",
    language: "tr",
    weather: "sunny",
    additional_notes: ""
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [step, setStep] = useState("upload") // upload | filter | result

  const handleImageUpload = (base64, previewUrl) => {
    setImage(base64)
    setPreview(previewUrl)
    setResult(null)
    setError(null)
    setStep("filter")
  }

  const handleRecommend = async () => {
    if (!image) return
    setLoading(true)
    setError(null)

    try {
      const response = await fetch("http://127.0.0.1:8003/outfit/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image, ...filters })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Bir hata oluştu")
      }

      const data = await response.json()
      setResult(data)
      setStep("result")
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setImage(null)
    setPreview(null)
    setResult(null)
    setError(null)
    setStep("upload")
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo" onClick={handleReset}>
            <span className="logo-symbol">◈</span>
            <span className="logo-text">AYNORA</span>
          </div>
          <p className="logo-tagline">AI Kombin Asistanınız</p>
        </div>
      </header>

      {/* Main */}
      <main className="main">
        {step === "upload" && (
          <UploadSection onUpload={handleImageUpload} />
        )}

        {step === "filter" && (
          <div className="filter-stage">
            {/* Uploaded image preview */}
            <div className="uploaded-preview">
              <div className="preview-label">Yüklenen Kıyafet</div>
              <img src={preview} alt="Yüklenen kıyafet" className="preview-img" />
              <button className="btn-ghost" onClick={handleReset}>
                Değiştir
              </button>
            </div>

            <FilterPanel
              filters={filters}
              onChange={setFilters}
              onSubmit={handleRecommend}
              loading={loading}
            />

            {error && <div className="error-msg">⚠ {error}</div>}
          </div>
        )}

        {step === "result" && result && (
          <OutfitResults
            result={result}
            preview={preview}
            onReset={handleReset}
            onBack={() => setStep("filter")}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 Aynora · Yapay Zeka Destekli Moda</p>
      </footer>
    </div>
  )
}
