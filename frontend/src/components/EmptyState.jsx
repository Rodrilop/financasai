/**
 * EmptyState — componente reutilizável de estado vazio com CTA
 * Props:
 *   icon      — string emoji ou SVG (default "📭")
 *   title     — título principal (obrigatório)
 *   subtitle  — texto secundário explicativo (opcional)
 *   actionLabel — texto do botão (opcional)
 *   onAction  — callback do botão (opcional)
 *   height    — altura do container (default "240px")
 */
export default function EmptyState({
  icon = '📭',
  title,
  subtitle,
  actionLabel,
  onAction,
  height = '240px',
}) {
  return (
    <div className="empty-state" style={{ minHeight: height }}>
      <div className="empty-state-icon">{icon}</div>
      <div className="empty-state-title">{title}</div>
      {subtitle && <div className="empty-state-subtitle">{subtitle}</div>}
      {actionLabel && onAction && (
        <button className="btn btn-primary btn-sm empty-state-btn" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  )
}
