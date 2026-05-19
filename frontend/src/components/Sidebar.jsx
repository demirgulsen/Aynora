/**
 * Sidebar.jsx
 * Sol sabit panel — aktif modüller + coming soon bölümü
 * Virtual try-on sidebar footer'da yer alıyor
 */

export default function Sidebar({ currentStep, onNavigate, onReset, isCollapsed, onToggle }) {
  const activeModules = [
    {
      id: "workspace",
      icon: "✂︎",
      label: "Kombin Oluştur",
      desc: "Görsel ve Akıllı Girdi",
      steps: ["upload", "filter", "result"],
    },
  ]

  const comingSoon = [
    {
      id: "studio",
      icon: "🧵✏️🎨︎",
      label: "Tasarım Atolyesi",
      desc: "Tasarımcılar için",
    },
    {
      id: "account",
      icon: "👤",
      label: "Moda Profilim",
      desc: "Profil & Stil DNA",
    },
    {
      id: "partner",
      icon: "🪞",
      label: "Ortaklıklar",
      desc: "İş Ortaklıkları",
    },
  ]

  const getActiveModule = () => {
    if (["upload", "filter"].includes(currentStep)) return "visual"
    if (currentStep === "chat") return "chat"
    if (currentStep === "result") return "result"
    return null
  }

  const activeModule = getActiveModule()

  const handleModuleClick = (moduleId) => {
    if (moduleId === "visual") onNavigate("upload")
    if (moduleId === "chat")   onNavigate("chat")
  }

  return (
    <aside className={`sidebar ${isCollapsed ? "collapsed" : ""}`}>
      {/* Logo */}
      <div className="sidebar-logo" onClick={onReset}>
         <span className="sidebar-logo-symbol">◈</span>
         {!isCollapsed && (
           <div className="sidebar-logo-text-group">
             <span className="sidebar-logo-name">AYNORA</span>
             <span className="sidebar-logo-tagline">AI Kombin Asistanı</span>
           </div>
         )}
       </div>

      {/* Aktif Modüller */}
      <div className="sidebar-section">
        <div className="sidebar-section-label">{isCollapsed ? "•" : "MODÜLLER"}</div>

        {activeModules.map((mod) => {
          const isActive = currentStep === "workspace" || currentStep === "result"

          return (
            <div
              key={mod.id}
              className={`sidebar-item ${isActive ? "active" : ""}`}
              onClick={() => onNavigate("workspace")}
              title={mod.label}
            >
              <span className="sidebar-item-icon">{mod.icon}</span>
              {!isCollapsed && (
                <div className="sidebar-item-meta">
                  <span className="sidebar-item-label">{mod.label}</span>
                  <span className="sidebar-item-desc">{mod.desc}</span>
                </div>
              )}
              {!isCollapsed && <span className="sidebar-badge new-badge">Aktif</span>}
            </div>
          )
        })}
      </div>

      {/* Coming Soon */}
      <div className="sidebar-section">
        <div className="sidebar-section-label">{isCollapsed ? "•" : "YAKINDA"}</div>

        {comingSoon.map((mod) => (
          <div
            key={mod.id}
            className="sidebar-item coming-soon"
            title={`${mod.label} — Yakında`}
          >
            <span className="sidebar-item-icon">{mod.icon}</span>
            {!isCollapsed && (
              <div className="sidebar-item-meta">
                <span className="sidebar-item-label">{mod.label}</span>
                <span className="sidebar-item-desc">{mod.desc}</span>
              </div>
            )}
            {!isCollapsed && <span className="sidebar-badge">Soon</span>}
          </div>
        ))}
      </div>

      {/* Virtual Try-On — Coming Soon */}
      <div className="sidebar-footer">
        <div className="sidebar-tryon-btn" title="Hadi Dene! — Sanal Kabin" onClick={() => onNavigate("tryon")}
            style={{ cursor: "pointer", opacity: 1 }}>
          <div className="sidebar-tryon-icon">🪞</div>
          {!isCollapsed && (
            <div className="sidebar-tryon-text">
              <div className="sidebar-tryon-title">Hadi Dene!</div>
              <div className="sidebar-tryon-sub">Sanal Kabin</div>
            </div>
          )}
          {!isCollapsed && (
            <div className="sidebar-badge" style={{ marginTop: "0.4rem", alignSelf: "center" }}>
              Soon
            </div>
          )}
        </div>
      </div>

    </aside>
  )
}