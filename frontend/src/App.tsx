import { useEffect, useState } from 'react'
import './App.css'
import { fetchHealth } from './lib/api'

function App() {
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [message, setMessage] = useState('Checking the RoadIQ backend connection...')

  useEffect(() => {
    const controller = new AbortController()

    fetchHealth(controller.signal)
      .then((health) => {
        setStatus('ok')
        setMessage(`${health.service} is reachable at ${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}.`)
      })
      .catch(() => {
        setStatus('error')
        setMessage('Backend not reachable yet. Configure VITE_API_BASE_URL to the running FastAPI service.')
      })

    return () => controller.abort()
  }, [])

  return (
    <main className="app-shell">
      <section className="status-card">
        <p className="eyebrow">RoadIQ</p>
        <h1>Road intelligence for safer journeys</h1>
        <p className="lede">
          This initial scaffold is focused on the project foundation: a runnable frontend,
          a versioned backend API, and the early structure for future road-scoring work.
        </p>

        <div className={`status-pill ${status}`}>
          {status === 'ok' && 'Backend healthy'}
          {status === 'error' && 'Backend unavailable'}
          {status === 'loading' && 'Checking backend...'}
        </div>

        <p className="status-text">{message}</p>

        <ul className="feature-list">
          <li>React + TypeScript + Vite frontend</li>
          <li>FastAPI backend with `/api/v1/health`</li>
          <li>Road-segment schema and sample fixture</li>
          <li>Documented architecture and scoring boundaries</li>
        </ul>
      </section>
    </main>
  )
}

export default App
