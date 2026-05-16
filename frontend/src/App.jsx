import { useState } from "react"
import { useStreamingRecommend } from "./hooks/useStreamingRecommend"
import LandingSection from "./components/LandingSection"
import UploadSection from "./components/UploadSection"
import ChatSection from "./components/ChatSection"
import FilterPanel from "./components/FilterPanel"
import OutfitResults from "./components/OutfitResults"
import LoadingStatus from "./components/LoadingStatus"
import "./index.css"

export default function App() {
  const [mode,        setMode]        = useState(null)
  const [image,       setImage]       = useState(null)
  const [preview,     setPreview]     = useState(null)
  const [filters,     setFilters]     = useState({
    concept: "casual", size: "M",
    color_preference: "no_preference",
    gender: "female", language: "tr",
    weather: "sunny", additional_notes: ""
  })
  const [chatMessage,  setChatMessage]  = useState("")
  const [chatHistory,  setChatHistory]  = useState([])
  const [step,         setStep]         = useState("landing")

  const {
    stage, stageMessage,
    analysis, assistantMessage,
    outfits, enrichedCount,
    done, error, isLoading,
    recommendVisual, recommendChat, reset: resetStream,
  } = useStreamingRecommend()

  // ── Handlers ─────────────────────────────────────────────

  const handleModeSelect = (m) => {
    setMode(m)
    setStep(m === "visual" ? "upload" : "chat")
  }

  const handleImageUpload = (base64, previewUrl) => {
    setImage(base64)
    setPreview(previewUrl)
    resetStream()
    setStep("filter")
  }

  const handleVisualRecommend = async () => {
    if (!image) return
    setStep("result")
    await recommendVisual(image, filters)
  }

  const handleChatRecommend = async (message) => {
    if (!message.trim()) return
    const newHistory = [...chatHistory, { role: "user", content: message }]
    setChatHistory(newHistory)
    setChatMessage("")
    setStep("result")
    await recommendChat(message, filters, chatHistory)
    if (assistantMessage) {
      setChatHistory(prev => [...prev, { role: "assistant", content: assistantMessage }])
    }
  }

  const handleReset = () => {
    setMode(null)
    setImage(null)
    setPreview(null)
    setChatMessage("")
    setChatHistory([])
    resetStream()
    setStep("landing")
  }

  const handleBack = () => {
    resetStream()
    setStep(mode === "visual" ? "filter" : "chat")
  }

  // ── Render ────────────────────────────────────────────────

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo" onClick={handleReset}>
            <span className="logo-symbol">◈</span>
            <span className="logo-text">AYNORA</span>
          </div>
          <p className="logo-tagline">AI Kombin Asistanınız</p>
        </div>
      </header>

      <main className="main">
        {step === "landing" && (
          <LandingSection onSelect={handleModeSelect} />
        )}

        {step === "upload" && (
          <UploadSection
            onUpload={handleImageUpload}
            onBack={() => setStep("landing")}
          />
        )}

        {step === "chat" && (
          <ChatSection
            filters={filters}
            onFiltersChange={setFilters}
            message={chatMessage}
            onMessageChange={setChatMessage}
            onSubmit={handleChatRecommend}
            chatHistory={chatHistory}
            loading={isLoading}
            error={error}
            onBack={() => setStep("landing")}
          />
        )}

        {step === "filter" && (
          <div className="filter-stage">
            <div className="uploaded-preview">
              <div className="preview-label">Yüklenen Kıyafet</div>
              <img src={preview} alt="Kıyafet" className="preview-img" />
              <button className="btn-ghost" onClick={() => setStep("upload")}>
                Değiştir
              </button>
            </div>
            <FilterPanel
              filters={filters}
              onChange={setFilters}
              onSubmit={handleVisualRecommend}
              loading={isLoading}
            />
          </div>
        )}

        {step === "result" && (
          <>
            {/* Loading status bar */}
            {isLoading && (
              <LoadingStatus
                stage={stage}
                message={stageMessage}
                enrichedCount={enrichedCount}
                totalCount={outfits.length}
              />
            )}

            {/* Error */}
            {error && <div className="error-msg">⚠ {error}</div>}

            {/* Results — show progressively as they stream in */}
            {(outfits.length > 0 || done) && (
              <OutfitResults
                outfits={outfits}
                analysis={analysis}
                assistantMessage={assistantMessage}
                preview={preview}
                mode={mode}
                isLoading={isLoading}
                onReset={handleReset}
                onBack={handleBack}
                onNewChat={() => { resetStream(); setStep("chat") }}
              />
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <p>© 2025 Aynora · Yapay Zeka Destekli Moda</p>
      </footer>
    </div>
  )
}