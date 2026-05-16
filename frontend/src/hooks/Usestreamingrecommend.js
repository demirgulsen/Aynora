/**
 * useStreamingRecommend.js
 * Custom hook for consuming SSE streaming recommendation endpoints.
 * Progressively updates UI as each pipeline stage completes.
 */

import { useState, useCallback, useRef } from "react"

const API_BASE = "http://127.0.0.1:8003"

export function useStreamingRecommend() {
  const [stage,            setStage]           = useState(null)
  const [stageMessage,     setStageMessage]    = useState("")
  const [analysis,         setAnalysis]        = useState(null)
  const [assistantMessage, setAssistantMessage]= useState("")
  const [outfits,          setOutfits]         = useState([])
  const [enrichedCount,    setEnrichedCount]   = useState(0)
  const [done,             setDone]            = useState(false)
  const [error,            setError]           = useState(null)
  const abortRef = useRef(null)

  const reset = useCallback(() => {
    setStage(null)
    setStageMessage("")
    setAnalysis(null)
    setAssistantMessage("")
    setOutfits([])
    setEnrichedCount(0)
    setDone(false)
    setError(null)
  }, [])

  const _consume = useCallback(async (endpoint, body) => {
    reset()

    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
        signal:  controller.signal,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Bir hata oluştu")
      }

      const reader  = response.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ""

      while (true) {
        const { done: streamDone, value } = await reader.read()
        if (streamDone) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split("\n\n")
        buffer = parts.pop() ?? ""

        for (const part of parts) {
          if (!part.trim()) continue

          const lines     = part.split("\n")
          const eventLine = lines.find(l => l.startsWith("event:"))
          const dataLine  = lines.find(l => l.startsWith("data:"))
          if (!eventLine || !dataLine) continue

          const event = eventLine.replace("event:", "").trim()
          const data  = JSON.parse(dataLine.replace("data:", "").trim())

          switch (event) {
            case "status":
              setStage(data.stage)
              setStageMessage(data.message)
              break
            case "analysis":
              setAnalysis(data.analysis)
              break
            case "assistant_message":
              setAssistantMessage(data.message)
              break
            case "outfits_raw":
              setOutfits(data.outfits.map(o => ({ ...o, _enriched: false })))
              break
            case "outfit_enriched":
              setOutfits(prev => {
                const next = [...prev]
                next[data.index] = { ...data.outfit, _enriched: true }
                return next
              })
              setEnrichedCount(prev => prev + 1)
              break
            case "done":
              setDone(true)
              setStage(null)
              break
            case "error":
              setError(data.message)
              setStage(null)
              break
          }
        }
      }
    } catch (e) {
      if (e.name !== "AbortError") {
        setError(e.message)
        setStage(null)
      }
    }
  }, [reset])

  const recommendVisual = useCallback((image, filters) =>
    _consume("/outfit/recommend/stream", { image, ...filters }), [_consume])

  const recommendChat = useCallback((message, filters, chatHistory) =>
    _consume("/outfit/chat-recommend/stream", {
      message, ...filters, chat_history: chatHistory,
    }), [_consume])

  return {
    stage, stageMessage,
    analysis, assistantMessage,
    outfits, enrichedCount,
    done, error,
    isLoading: stage !== null,
    recommendVisual, recommendChat, reset,
  }
}