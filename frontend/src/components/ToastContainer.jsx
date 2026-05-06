import { useEffect, useState, useContext } from 'react'
import { createPortal } from 'react-dom'
import { ToastContext } from '../contexts/ToastContext'

const ICONS = {
  success: '✅',
  error:   '❌',
  info:    'ℹ️',
  warning: '⚠️',
}

function Toast({ id, message, type, duration, onRemove }) {
  const [exiting, setExiting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setExiting(true)
      setTimeout(() => onRemove(id), 320)
    }, duration)
    return () => clearTimeout(timer)
  }, [id, duration, onRemove])

  return (
    <div className={`toast toast-${type}${exiting ? ' toast-exit' : ''}`}>
      <span className="toast-icon">{ICONS[type]}</span>
      <span className="toast-message">{message}</span>
      <button
        className="toast-close"
        onClick={() => { setExiting(true); setTimeout(() => onRemove(id), 320) }}
        aria-label="Fechar"
      >
        ×
      </button>
      <div className="toast-progress" style={{ animationDuration: `${duration}ms` }} />
    </div>
  )
}

export default function ToastContainer() {
  const { toasts, removeToast } = useContext(ToastContext)

  return createPortal(
    <div className="toast-container" aria-live="polite" aria-atomic="false">
      {toasts.map(t => (
        <Toast key={t.id} {...t} onRemove={removeToast} />
      ))}
    </div>,
    document.body
  )
}
