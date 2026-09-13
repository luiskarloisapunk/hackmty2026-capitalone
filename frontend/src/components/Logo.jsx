// Marca propia: una onda (temporadas irregulares) que se aplana en una
// línea recta (ingreso regularizado) -- la metáfora "AC/DC" del producto,
// no el logo de Capital One (no tenemos una fuente confiable de ese asset
// en este entorno; el crédito a Capital One va como texto en el layout).
export function Logo({ size = 28 }) {
  const height = Math.round(size * (40 / 120))

  return (
    <svg
      width={size}
      height={height}
      viewBox="0 0 120 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="acdc-logo-gradient" x1="0" y1="0" x2="120" y2="0" gradientUnits="userSpaceOnUse">
          <stop offset="0" style={{ stopColor: 'var(--color-accent)' }} />
          <stop offset="0.5" style={{ stopColor: 'var(--color-accent)' }} />
          <stop offset="0.68" style={{ stopColor: 'var(--color-primary)' }} />
          <stop offset="1" style={{ stopColor: 'var(--color-primary)' }} />
        </linearGradient>
      </defs>
      <path
        d="M0,20 C6,4 14,4 20,20 C26,36 34,36 40,20 C46,4 54,4 60,20 L120,20"
        stroke="url(#acdc-logo-gradient)"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
