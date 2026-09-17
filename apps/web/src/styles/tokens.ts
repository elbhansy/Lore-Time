/**
 * Phase 6.1 Design Tokens
 * 
 * Aesthetic Direction: Dark, Cinematic, Editorial, Information-Dense, Structured.
 * Non-Negotiable: No neon AI dashboard clutter, no excessive cards, no raw magic numbers.
 */

export const tokens = {
  colors: {
    // Canvas & Surfaces
    canvas: '#090a0f',
    surfacePrimary: '#11131a',
    surfaceSecondary: '#161922',
    surfaceElevated: '#1e2230',
    surfaceOverlay: 'rgba(9, 10, 15, 0.82)',

    // Borders & Dividers
    borderSubtle: '#232736',
    borderDefault: '#2f3548',
    borderStrong: '#444d66',
    borderFocus: '#6366f1',

    // Typography
    textPrimary: '#f1f5f9',
    textSecondary: '#94a3b8',
    textMuted: '#64748b',
    textInverse: '#0f172a',

    // Brand / Semantic Accents (Editorial, Deep Indigo & Amber)
    accentPrimary: '#6366f1',
    accentPrimaryHover: '#4f46e5',
    accentSecondary: '#8b5cf6',
    
    // Status & Feedback
    statusSuccess: '#10b981',
    statusSuccessBg: 'rgba(16, 185, 129, 0.12)',
    statusWarning: '#f59e0b',
    statusWarningBg: 'rgba(245, 158, 11, 0.12)',
    statusError: '#ef4444',
    statusErrorBg: 'rgba(239, 68, 68, 0.12)',
    statusInfo: '#38bdf8',
    statusInfoBg: 'rgba(56, 189, 248, 0.12)',

    // Temporal Horizon Indicator
    temporalScope: '#d97706',
    temporalScopeGlow: 'rgba(217, 119, 6, 0.18)',
  },

  typography: {
    fontFamily: {
      sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      mono: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
      editorial: "Georgia, Cambria, 'Times New Roman', Times, serif",
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.84375rem', // 13.5px
      base: '0.9375rem',// 15px
      md: '1.0625rem',  // 17px
      lg: '1.25rem',    // 20px
      xl: '1.5rem',     // 24px
      '2xl': '1.875rem',// 30px
      '3xl': '2.25rem', // 36px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.625,
    },
  },

  spacing: {
    none: '0',
    '3xs': '0.125rem', // 2px
    '2xs': '0.25rem',  // 4px
    xs: '0.5rem',     // 8px
    sm: '0.75rem',    // 12px
    md: '1rem',       // 16px
    lg: '1.5rem',     // 24px
    xl: '2rem',       // 32px
    '2xl': '3rem',    // 48px
  },

  borderRadius: {
    none: '0',
    xs: '2px',
    sm: '4px',
    md: '6px',
    lg: '8px',
    full: '9999px',
  },

  shadows: {
    none: 'none',
    sm: '0 1px 3px rgba(0, 0, 0, 0.4)',
    md: '0 4px 12px rgba(0, 0, 0, 0.5)',
    lg: '0 10px 25px rgba(0, 0, 0, 0.65)',
    elevation1: '0 1px 2px rgba(0, 0, 0, 0.4), 0 0 0 1px #232736',
    elevation2: '0 4px 16px rgba(0, 0, 0, 0.6), 0 0 0 1px #2f3548',
  },

  transitions: {
    fast: '100ms ease-out',
    normal: '180ms cubic-bezier(0.16, 1, 0.3, 1)',
    slow: '300ms cubic-bezier(0.16, 1, 0.3, 1)',
  },

  zIndex: {
    base: 0,
    header: 50,
    sidebar: 40,
    inspector: 40,
    overlay: 90,
    modal: 100,
    popover: 110,
    tooltip: 120,
  },

  layout: {
    sidebarWidth: '240px',
    inspectorWidth: '340px',
    headerHeight: '52px',
    systemBarHeight: '28px',
    maxContentWidth: '1600px',
  },

  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  }
} as const;

export type DesignTokens = typeof tokens;
