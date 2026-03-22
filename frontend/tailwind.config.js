/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
                heading: ['Inter', 'sans-serif'],
                serif: ['Instrument Serif', 'Georgia', 'serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            colors: {
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))'
                },
                /* InFinea brand tokens */
                brand: {
                    primary: '#275255',
                    teal: '#459492',
                    secondary: '#55B3AE',
                    green: '#5DB786',
                    coral: '#E48C75',
                },
                /* Category tokens — brand-aligned */
                learning: '#459492',
                productivity: '#E48C75',
                'well-being': '#5DB786',
                /* State tokens */
                success: '#5DB786',
                warning: '#E48C75',
                info: '#459492',
                /* Surface elevation system */
                surface: {
                    0: 'hsl(var(--surface-0))',
                    1: 'hsl(var(--surface-1))',
                    2: 'hsl(var(--surface-2))',
                    3: 'hsl(var(--surface-3))',
                },
                /* Dark section palette — Revolut-inspired */
                dark: {
                    DEFAULT: '#275255',
                    deep: '#1F3F42',
                    deeper: '#163233',
                    lighter: '#2F6669',
                    muted: 'rgba(255, 255, 255, 0.7)',
                    subtle: 'rgba(255, 255, 255, 0.5)',
                },
            },
            boxShadow: {
                /* Système d'élévation progressif — teal-tinted */
                'xs': '0 1px 2px rgba(39,82,85,0.05)',
                'card': '0 1px 3px rgba(39,82,85,0.05), 0 1px 2px rgba(39,82,85,0.03), 0 0 0 1px rgba(69,148,146,0.06)',
                'card-hover': '0 4px 12px rgba(39,82,85,0.08), 0 2px 4px rgba(39,82,85,0.05), 0 0 0 1px rgba(69,148,146,0.14)',
                'card-elevated': '0 8px 28px rgba(39,82,85,0.10), 0 4px 8px rgba(39,82,85,0.05), 0 0 0 1px rgba(69,148,146,0.12)',
                'premium': '0 12px 40px rgba(39,82,85,0.15), 0 4px 12px rgba(39,82,85,0.08), 0 0 0 1px rgba(69,148,146,0.15), 0 0 24px rgba(69,148,146,0.06)',
                'stat': '0 1px 3px rgba(39,82,85,0.05), 0 0 0 1px rgba(69,148,146,0.06)',
                'stat-hover': '0 4px 16px rgba(39,82,85,0.08), 0 0 0 1px rgba(69,148,146,0.14), 0 0 12px rgba(69,148,146,0.05)',
                'dark-card': '0 2px 8px rgba(0,0,0,0.15), 0 8px 24px rgba(0,0,0,0.10)',
                /* Glows — stronger teal presence */
                'glow-teal': '0 0 0 1px rgba(69,148,146,0.20), 0 4px 24px rgba(69,148,146,0.12), 0 0 16px rgba(69,148,146,0.06)',
                'glow-coral': '0 0 0 1px rgba(228,140,117,0.20), 0 4px 24px rgba(228,140,117,0.12), 0 0 16px rgba(228,140,117,0.06)',
                'glow-green': '0 0 0 1px rgba(93,183,134,0.20), 0 4px 24px rgba(93,183,134,0.12), 0 0 16px rgba(93,183,134,0.06)',
                /* Inner highlights — teal-tinted depth */
                'inner-highlight': 'inset 0 1px 0 rgba(255,255,255,0.8), 0 1px 3px rgba(39,82,85,0.05), 0 4px 12px rgba(39,82,85,0.04)',
                'inner-highlight-hover': 'inset 0 1px 0 rgba(255,255,255,0.9), 0 4px 12px rgba(39,82,85,0.08), 0 8px 24px rgba(39,82,85,0.05), 0 0 0 1px rgba(69,148,146,0.10)',
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' }
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' }
                },
                'fade-in': {
                    from: { opacity: '0', transform: 'translateY(8px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                },
                'slide-in': {
                    from: { transform: 'translateX(-100%)' },
                    to: { transform: 'translateX(0)' }
                },
                'pulse-glow': {
                    '0%, 100%': { boxShadow: '0 0 20px rgba(69, 148, 146, 0.2)' },
                    '50%': { boxShadow: '0 0 40px rgba(69, 148, 146, 0.35)' }
                },
                'scale-in': {
                    from: { opacity: '0', transform: 'scale(0.95)' },
                    to: { opacity: '1', transform: 'scale(1)' }
                },
                'slide-up': {
                    from: { opacity: '0', transform: 'translateY(16px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-6px)' }
                },
                'shimmer': {
                    from: { backgroundPosition: '-200% 0' },
                    to: { backgroundPosition: '200% 0' }
                },
                'enter': {
                    from: { opacity: '0', transform: 'translateY(6px) scale(0.98)' },
                    to: { opacity: '1', transform: 'translateY(0) scale(1)' }
                },
                'subtle-bounce': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-3px)' }
                },
                'progress-fill': {
                    from: { width: '0%' },
                    to: { width: 'var(--progress-width, 100%)' }
                },
                'glow-breathe': {
                    '0%, 100%': { boxShadow: '0 0 0 0 rgba(69, 148, 146, 0)' },
                    '50%': { boxShadow: '0 0 20px 4px rgba(69, 148, 146, 0.1)' }
                },
                'counter-up': {
                    from: { opacity: '0', transform: 'translateY(8px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                },
                /* === Micro-interactions keyframes === */
                'tab-slide-in': {
                    from: { opacity: '0', transform: 'translateX(8px)' },
                    to: { opacity: '1', transform: 'translateX(0)' }
                },
                'tab-slide-out': {
                    from: { opacity: '1', transform: 'translateX(0)' },
                    to: { opacity: '0', transform: 'translateX(-8px)' }
                },
                'modal-enter': {
                    from: { opacity: '0', transform: 'scale(0.96) translateY(8px)' },
                    to: { opacity: '1', transform: 'scale(1) translateY(0)' }
                },
                'modal-overlay-enter': {
                    from: { opacity: '0', backdropFilter: 'blur(0px)' },
                    to: { opacity: '1', backdropFilter: 'blur(8px)' }
                },
                'ripple': {
                    to: { transform: 'scale(2.5)', opacity: '0' }
                },
                'success-pop': {
                    '0%': { transform: 'scale(0.8)', opacity: '0' },
                    '50%': { transform: 'scale(1.08)' },
                    '100%': { transform: 'scale(1)', opacity: '1' }
                },
                'success-check': {
                    '0%': { strokeDashoffset: '24' },
                    '100%': { strokeDashoffset: '0' }
                },
                'confetti-fall': {
                    '0%': { transform: 'translateY(-10px) rotate(0deg)', opacity: '1' },
                    '100%': { transform: 'translateY(40px) rotate(360deg)', opacity: '0' }
                },
                'slide-down-fade': {
                    from: { opacity: '0', transform: 'translateY(-4px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                },
                'slide-up-fade': {
                    from: { opacity: '0', transform: 'translateY(4px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                },
                'expand': {
                    from: { opacity: '0', height: '0', transform: 'scaleY(0.95)' },
                    to: { opacity: '1', height: 'var(--expand-height, auto)', transform: 'scaleY(1)' }
                },
                'number-tick': {
                    '0%': { transform: 'translateY(100%)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' }
                },
                'shake': {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '20%, 60%': { transform: 'translateX(-3px)' },
                    '40%, 80%': { transform: 'translateX(3px)' }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'fade-in': 'fade-in 0.4s ease-out forwards',
                'slide-in': 'slide-in 0.3s ease-out',
                'pulse-glow': 'pulse-glow 3s ease-in-out infinite',
                'scale-in': 'scale-in 0.2s ease-out',
                'slide-up': 'slide-up 0.4s ease-out forwards',
                'float': 'float 4s ease-in-out infinite',
                'shimmer': 'shimmer 2s linear infinite',
                'enter': 'enter 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'subtle-bounce': 'subtle-bounce 3s ease-in-out infinite',
                'progress-fill': 'progress-fill 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'glow-breathe': 'glow-breathe 3s ease-in-out infinite',
                'counter-up': 'counter-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                /* Micro-interactions */
                'tab-slide-in': 'tab-slide-in 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'modal-enter': 'modal-enter 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'modal-overlay': 'modal-overlay-enter 0.2s ease-out forwards',
                'success-pop': 'success-pop 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'success-check': 'success-check 0.3s ease-out 0.2s forwards',
                'confetti': 'confetti-fall 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'slide-down-fade': 'slide-down-fade 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'slide-up-fade': 'slide-up-fade 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'expand': 'expand 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'number-tick': 'number-tick 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'shake': 'shake 0.4s ease-in-out'
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
};
