import type { Config } from 'tailwindcss';

/**
 * Los colores no se escriben aqui como literales: apuntan a las variables CSS
 * definidas en `src/styles/tokens.css`. Cambiar el tema (por ejemplo, pegar la
 * paleta exportada desde el proyecto de diseno) es editar UN archivo, sin tocar
 * ningun componente.
 */
const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          base: 'var(--surface-base)',
          raised: 'var(--surface-raised)',
          overlay: 'var(--surface-overlay)',
          sunken: 'var(--surface-sunken)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          strong: 'var(--border-strong)',
        },
        content: {
          primary: 'var(--content-primary)',
          secondary: 'var(--content-secondary)',
          muted: 'var(--content-muted)',
          inverse: 'var(--content-inverse)',
        },
        brand: {
          DEFAULT: 'var(--brand)',
          soft: 'var(--brand-soft)',
          strong: 'var(--brand-strong)',
        },
        status: {
          pending: 'var(--status-pending)',
          transit: 'var(--status-transit)',
          delivered: 'var(--status-delivered)',
          failed: 'var(--status-failed)',
          warning: 'var(--status-warning)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      borderRadius: {
        card: 'var(--radius-card)',
        control: 'var(--radius-control)',
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        overlay: 'var(--shadow-overlay)',
      },
    },
  },
  plugins: [],
};

export default config;
