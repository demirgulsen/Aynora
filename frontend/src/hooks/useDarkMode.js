import { useState, useEffect } from "react"

export function useDarkMode() {
  // 1. LocalStorage veya Sistem Tercihine göre ilk temayı belirle
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("aynora_theme")
    if (saved) return saved

    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches
    return prefersLight ? "light" : "dark"
  })

  // 2. Tema her değiştiğinde HTML sınıfını ve localStorage'ı güncelle
  useEffect(() => {
    const root = document.documentElement // ya da document.body
    if (theme === "light") {
      root.classList.add("light-mode")
    } else {
      root.classList.remove("light-mode")
    }
    localStorage.setItem("aynora_theme", theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === "dark" ? "light" : "dark"))
  }

  return { theme, toggleTheme, isLight: theme === "light" }
}