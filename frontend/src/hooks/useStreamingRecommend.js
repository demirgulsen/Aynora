import { useState, useCallback, useRef } from "react"

const API_BASE = "http://127.0.0.1:8003"

async function consumeStream(endpoint, body, handlers, signal) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.detail || "Bir hata oluştu")
  }

  const reader  = response.body.getReader()
  const decoder = new TextDecoder()
  let   buffer  = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

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
      handlers[event]?.(data)
    }
  }
}

export function useStreamingRecommend() {
  const [stage,            setStage]           = useState(null)
  const [analysis,         setAnalysis]        = useState(null)
  const [assistantMessage, setAssistantMessage]= useState("")
  const [outfits,          setOutfits]         = useState([])
  const [enrichedCount,    setEnrichedCount]   = useState(0)
  const [error,            setError]           = useState(null)
  const [loadingMore,      setLoadingMore]     = useState(false)
  const abortRef = useRef(null)

  const reset = useCallback(() => {
    setStage(null)
    setAnalysis(null)
    setAssistantMessage("")
    setOutfits([])
    setEnrichedCount(0)
    setError(null)
  }, [])

  const _handlers = useCallback((append = false) => ({
    status:            ({ stage })   => setStage(stage),
    analysis:          ({ analysis })=> setAnalysis(analysis),
    assistant_message: ({ message }) => setAssistantMessage(message),
    outfits_raw: ({ outfits }) => {
      const raw = outfits.map(o => ({ ...o, _enriched: false }))
      setOutfits(prev => append ? [...prev, ...raw] : raw)
    },
    outfit_enriched: ({ index, outfit }) => {
      setOutfits(prev => {
        const next = [...prev]
        const i    = append ? prev.length - outfits.length + index : index
        if (next[i]) next[i] = { ...outfit, _enriched: true }
        return next
      })
      setEnrichedCount(prev => prev + 1)
    },
    done:  () => setStage(null),
    error: ({ message }) => { setError(message); setStage(null) },
  }), [])

  const _run = useCallback(async (endpoint, body, append = false) => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      // Track new outfits count for append mode
      let newCount = 0
      const handlers = {
        status:            ({ stage })   => setStage(stage),
        analysis:          ({ analysis })=> setAnalysis(analysis),
        assistant_message: ({ message }) => setAssistantMessage(message),
        outfits_raw: ({ outfits: raw }) => {
          newCount = raw.length
          const mapped = raw.map(o => ({ ...o, _enriched: false }))
          setOutfits(prev => append ? [...prev, ...mapped] : mapped)
        },
        outfit_enriched: ({ index, outfit }) => {
          setOutfits(prev => {
            const next = [...prev]
            const i    = append ? prev.length - newCount + index : index
            if (next[i]) next[i] = { ...outfit, _enriched: true }
            return next
          })
          if (!append) setEnrichedCount(prev => prev + 1)
        },
        done:  () => setStage(null),
        error: ({ message }) => { setError(message); setStage(null) },
      }

      await consumeStream(endpoint, body, handlers, controller.signal)
    } catch (e) {
      if (e.name !== "AbortError") {
        setError(e.message)
        setStage(null)
      }
    }
  }, [])

  const recommendVisual = useCallback((image, filters) => {
    reset()
    return _run("/outfit/recommend/stream", { image, ...filters }, false)
  }, [_run, reset])

  const recommendChat = useCallback((message, filters, chatHistory) => {
    reset()
    return _run("/outfit/chat-recommend/stream", {
      message, ...filters, chat_history: chatHistory,
    }, false)
  }, [_run, reset])

  const loadMore = useCallback((endpoint, body) => {
    setLoadingMore(true)
    return _run(endpoint, body, true).finally(() => setLoadingMore(false))
  }, [_run])

  return {
    stage, analysis, assistantMessage,
    outfits, enrichedCount,
    error, loadingMore,
    isLoading:  stage !== null,
    recommendVisual, recommendChat,
    loadMore, reset,
  }
}