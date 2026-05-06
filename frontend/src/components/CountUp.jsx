import { useEffect, useRef, useState } from 'react'

/**
 * CountUp — anima um número de 0 até `end` quando montado.
 * Props:
 *   end       — valor final (número)
 *   duration  — duração da animação em ms (default 1200)
 *   prefix    — prefixo (ex: "R$ ")
 *   suffix    — sufixo (ex: "%")
 *   decimals  — casas decimais (default 0)
 *   locale    — locale para formatação (default "pt-BR")
 */
export default function CountUp({
  end,
  duration = 1200,
  prefix = '',
  suffix = '',
  decimals = 0,
  locale = 'pt-BR',
}) {
  const [display, setDisplay] = useState(0)
  const rafRef = useRef(null)
  const startRef = useRef(null)
  const endVal = parseFloat(end) || 0

  useEffect(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    startRef.current = null

    const animate = (timestamp) => {
      if (!startRef.current) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(eased * endVal)
      if (progress < 1) rafRef.current = requestAnimationFrame(animate)
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [endVal, duration])

  const formatted = display.toLocaleString(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })

  return <span>{prefix}{formatted}{suffix}</span>
}
