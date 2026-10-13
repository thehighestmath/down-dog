import type { CSSProperties } from 'react'

export function btnStyle(bg: string): CSSProperties {
  return {
    background: bg,
    color: '#fff',
    border: 'none',
    padding: '10px 16px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
  }
}
