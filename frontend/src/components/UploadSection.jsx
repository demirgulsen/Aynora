import { useState, useRef } from "react"

export default function UploadSection({ onUpload }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const processFile = (file) => {
    if (!file || !file.type.startsWith("image/")) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const base64Full = e.target.result           // data:image/jpeg;base64,...
      const base64 = base64Full.split(",")[1]      // sadece base64 kısmı
      const previewUrl = URL.createObjectURL(file)
      onUpload(base64, previewUrl)
    }
    reader.readAsDataURL(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    processFile(e.dataTransfer.files[0])
  }

  const handleChange = (e) => processFile(e.target.files[0])

  return (
    <div className="upload-page">
      <div className="upload-hero">
        <h1 className="hero-title">
          Kıyafetini Yükle<br />
          <span className="hero-accent">Kombinini Keşfet</span>
        </h1>
        <p className="hero-sub">
          Yapay zeka, kıyafetini analiz ederek sana özel<br />
          kombin önerileri sunar.
        </p>
      </div>

      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleChange}
          style={{ display: "none" }}
        />
        <div className="dropzone-icon">◈</div>
        <p className="dropzone-text">
          Kıyafet fotoğrafını buraya sürükle<br />
          <span className="dropzone-sub">veya tıklayarak seç</span>
        </p>
        <p className="dropzone-formats">JPG · PNG · WEBP</p>
      </div>

      <div className="upload-tips">
        <div className="tip">
          <span className="tip-icon">◎</span>
          <span>Tek bir kıyafet parçası yükle</span>
        </div>
        <div className="tip">
          <span className="tip-icon">◎</span>
          <span>Düz arka plan tercih et</span>
        </div>
        <div className="tip">
          <span className="tip-icon">◎</span>
          <span>Net ve aydınlık bir fotoğraf kullan</span>
        </div>
      </div>
    </div>
  )
}
