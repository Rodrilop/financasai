import { createContext, useContext, useState, useCallback, useRef } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const counterRef = useRef(0)

  const addToast = useCallback((message, type = 'success', duration = 3500) => {
    const id = ++counterRef.current
    setToasts(prev => [...prev, { id, message, type, duration }])
    return id
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast, removeToast, toasts }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')

  return {
    success: (msg, duration) => ctx.addToast(msg, 'success', duration),
    error:   (msg, duration) => ctx.addToast(msg, 'error',   duration),
    info:    (msg, duration) => ctx.addToast(msg, 'info',    duration),
    warning: (msg, duration) => ctx.addToast(msg, 'warning', duration),
    remove:  (id)            => ctx.removeToast(id),
  }
}

export { ToastContext }
