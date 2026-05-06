/** Skeleton base — pulsa com shimmer enquanto carrega */
function SkeletonBase({ width = '100%', height = '16px', radius = '6px', style = {} }) {
  return (
    <div
      className="skeleton"
      style={{ width, height, borderRadius: radius, ...style }}
    />
  )
}

/** Skeleton de um card de métrica (4 linhas: ícone, label, valor, sub) */
export function SkeletonCard() {
  return (
    <div className="card" style={{ gap: 10 }}>
      <SkeletonBase width="36px" height="36px" radius="10px" style={{ marginBottom: 4 }} />
      <SkeletonBase width="60%" height="11px" />
      <SkeletonBase width="80%" height="28px" radius="8px" style={{ margin: '6px 0 4px' }} />
      <SkeletonBase width="50%" height="11px" />
    </div>
  )
}

/** Skeleton de uma tabela (header + N linhas) */
export function SkeletonTable({ rows = 5 }) {
  return (
    <div style={{ padding: '0 0 8px' }}>
      <div style={{ display: 'flex', gap: 12, padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
        {[40, 120, 80, 70, 60, 60].map((w, i) => (
          <SkeletonBase key={i} width={`${w}px`} height="11px" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          style={{
            display: 'flex', gap: 12,
            padding: '14px 16px',
            borderBottom: i < rows - 1 ? '1px solid var(--border)' : 'none',
            opacity: 1 - i * 0.12,
          }}
        >
          {[40, 120, 80, 70, 60, 60].map((w, j) => (
            <SkeletonBase key={j} width={`${w}px`} height="13px" />
          ))}
        </div>
      ))}
    </div>
  )
}

/** Skeleton de um gráfico (círculo + legenda) */
export function SkeletonChart({ height = 240 }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: 8 }}>
      <SkeletonBase width={`${height * 0.8}px`} height={`${height * 0.8}px`} radius="50%" />
      <div style={{ display: 'flex', gap: 12 }}>
        {[70, 90, 60].map((w, i) => (
          <SkeletonBase key={i} width={`${w}px`} height="11px" />
        ))}
      </div>
    </div>
  )
}

/** Skeleton de cards de métricas (grade de 4) */
export function SkeletonCardsGrid({ count = 4 }) {
  return (
    <div className="cards-grid">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}
