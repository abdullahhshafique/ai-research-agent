# Design — AI Research Agent

## Design System

No external design system or Figma file exists yet. This document is the source of truth. Components are hand-authored HTML/CSS using the token values below.

---

## Colour Tokens

### Dark Theme (default)

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#0F172A` | Page background |
| `--bg-surface` | `#1E293B` | Cards, panels |
| `--bg-elevated` | `#334155` | Hover states, inputs |
| `--text-primary` | `#F1F5F9` | Body text, headings |
| `--text-secondary` | `#94A3B8` | Labels, captions |
| `--text-muted` | `#64748B` | Placeholders, disabled |
| `--accent` | `#3B82F6` | Primary actions, links, progress |
| `--accent-hover` | `#2563EB` | Button hover |
| `--success` | `#22C55E` | Completed status |
| `--warning` | `#F59E0B` | Processing status |
| `--error` | `#EF4444` | Failed status, errors |
| `--border` | `#334155` | Dividers, input borders |

### Light Theme

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#F8FAFC` | Page background |
| `--bg-surface` | `#FFFFFF` | Cards, panels |
| `--bg-elevated` | `#F1F5F9` | Hover states, inputs |
| `--text-primary` | `#0F172A` | Body text, headings |
| `--text-secondary` | `#475569` | Labels, captions |
| `--text-muted` | `#94A3B8` | Placeholders, disabled |
| `--accent` | `#2563EB` | Primary actions, links |
| `--border` | `#E2E8F0` | Dividers, input borders |

Theme is stored in `Profile.theme` (dark/light) and applied via a `data-theme` attribute on `<html>`.

User-customisable accent colour stored in `Profile.accent_color` (hex, default `#3B82F6`).

---

## Typography

| Role | Font | Weight | Size |
|---|---|---|---|
| Display heading | System UI / Inter | 700 | 2rem (32px) |
| Section heading | System UI / Inter | 600 | 1.5rem (24px) |
| Sub-heading | System UI / Inter | 600 | 1.125rem (18px) |
| Body | System UI / Inter | 400 | 1rem (16px) |
| Small / caption | System UI / Inter | 400 | 0.875rem (14px) |
| Code / monospace | `ui-monospace, 'Cascadia Code', monospace` | 400 | 0.875rem |

Line height: 1.6 for body, 1.2 for headings. Letter spacing: normal for body, `-0.02em` for headings.

Font stack (no external font load — system fonts only for performance):
```css
font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
             'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

---

## Spacing & Layout Grid

Base unit: `4px` (0.25rem).

| Scale | Value | Usage |
|---|---|---|
| `xs` | 4px | Icon gaps, tight padding |
| `sm` | 8px | Input padding, badge padding |
| `md` | 16px | Card padding, form field gap |
| `lg` | 24px | Section gap |
| `xl` | 32px | Page section gap |
| `2xl` | 48px | Hero spacing |

Layout: single-column centred, max-width `768px` for content, `1200px` for dashboard.

Breakpoints:
| Name | Min width | Behaviour |
|---|---|---|
| `sm` | 640px | Two-column form layout |
| `md` | 768px | Sidebar visible |
| `lg` | 1024px | Full dashboard layout |

---

## Iconography

No icon library dependency. Use inline SVG for all icons. Icon sizes: `16px` (inline), `20px` (button), `24px` (standalone). Stroke width: `1.5px`. Style: outline (not filled) for consistency.

Common icons needed: search, download, refresh, clock, check, x-circle, alert-triangle, user, settings, log-out.

---

## UI Components

### Buttons

| Variant | Background | Text | Border |
|---|---|---|---|
| Primary | `--accent` | white | none |
| Secondary | transparent | `--accent` | `1px solid --accent` |
| Ghost | transparent | `--text-secondary` | none |
| Danger | `--error` | white | none |
| Disabled | `--bg-elevated` | `--text-muted` | none |

States: hover (darken 10%), active (darken 15%), focus (2px outline `--accent` offset 2px), disabled (opacity 0.5, cursor not-allowed).

Sizes: `sm` (px-3 py-1.5 text-sm), `md` (px-4 py-2), `lg` (px-6 py-3 text-lg).

Border radius: `6px` (default), `4px` (sm), `8px` (lg).

### Inputs & Textarea

- Background: `--bg-elevated`
- Border: `1px solid --border`
- Focus border: `--accent`
- Border radius: `6px`
- Padding: `8px 12px`
- Error state: border `--error`, helper text in `--error` below field
- Disabled: opacity 0.5

### Cards

- Background: `--bg-surface`
- Border: `1px solid --border`
- Border radius: `8px`
- Padding: `16px` (sm), `24px` (md)
- Box shadow: `0 1px 3px rgba(0,0,0,0.12)`

### Progress Bar

- Track: `--bg-elevated`
- Fill: `--accent`
- Height: `8px`
- Border radius: `4px`
- `role="progressbar"` with `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`
- Animated fill transition: `width 0.3s ease`

### Status Badges

| Status | Background | Text |
|---|---|---|
| pending | `--bg-elevated` | `--text-muted` |
| processing | amber-100 / amber-900 | amber |
| completed | green-100 / green-900 | `--success` |
| failed | red-100 / red-900 | `--error` |

### Modals

- Backdrop: `rgba(0,0,0,0.5)` with `backdrop-filter: blur(2px)`
- Panel: `--bg-surface`, border-radius `12px`, max-width `480px`
- Close button: top-right, ghost variant
- Focus trap: first focusable element on open; `Escape` closes

---

## Motion & Animations

- Duration: `150ms` (micro), `250ms` (standard), `400ms` (page transition)
- Easing: `ease-out` for entrances, `ease-in` for exits, `ease-in-out` for transforms
- Progress bar fill: `transition: width 300ms ease`
- Toast/notification slide-in: `translateY(-8px)` → `translateY(0)` over `250ms ease-out`
- Spinner: `rotate 1s linear infinite`
- Respect `prefers-reduced-motion`: wrap all animations in `@media (prefers-reduced-motion: no-preference)`

---

## Imagery & Illustration Style

- No decorative illustrations in MVP
- Screenshots/demo images: use actual app screenshots, not stock photos
- Avoid gradients on interactive elements (use flat colour)
- Gradient allowed on hero/landing section only: `linear-gradient(135deg, #1E293B, #0F172A)`

---

## Voice & Tone

- **Personality:** Calm, professional, direct. Not playful or casual.
- **Error messages:** Specific and actionable. "Search returned no results — try a broader query." Not "Something went wrong."
- **Progress messages:** Present tense, active. "Searching the web…", "Summarising sources…", "Generating report…"
- **Empty states:** Encouraging. "No research yet — submit your first query above."
- **Quota messages:** Factual, not punitive. "You've used 10 of 10 queries this hour. Resets at 14:30."

---

## Dark Mode / Theming

- Default: dark theme
- Toggle stored in `Profile.theme`; applied as `data-theme="dark"` or `data-theme="light"` on `<html>`
- CSS custom properties defined under `:root[data-theme="dark"]` and `:root[data-theme="light"]`
- System preference respected on first visit if no profile preference set: `@media (prefers-color-scheme: light)`
- Accent colour override: `--accent` replaced with `Profile.accent_color` via inline style on `<html>`

---

## Accessibility Design

- Focus indicators: `outline: 2px solid var(--accent); outline-offset: 2px` on all interactive elements — never `outline: none` without a custom replacement
- Touch targets: minimum `44×44px` for all interactive elements
- Colour contrast: ≥ 4.5:1 for normal text, ≥ 3:1 for large text and UI components (verified against both themes)
- Reading order: DOM order matches visual order; no `tabindex > 0`
- Form labels: every input has an associated `<label>` (not just placeholder)
- Error messages: linked to input via `aria-describedby`
- Progress bar: `role="progressbar"` with live region `aria-live="polite"` for status updates
- Skip link: `<a href="#main-content" class="sr-only focus:not-sr-only">Skip to content</a>` at top of every page

---

## Responsive & Adaptive Behaviour

| Viewport | Layout changes |
|---|---|
| < 640px | Single column; nav collapses to hamburger; cards full-width |
| 640–768px | Two-column form; sidebar hidden |
| 768–1024px | Sidebar visible; content max-width 768px |
| > 1024px | Full dashboard layout; max-width 1200px |

Hide non-critical columns in history table on mobile (keep: query text, status, date).
PDF download button always visible regardless of viewport.

---

## Brand Assets

- Logo: text-based wordmark "Research Agent" in `--text-primary`, weight 700
- Favicon: simple magnifying glass SVG, 32×32, `--accent` fill on `--bg-primary` background
- No external logo files committed — generate programmatically or add to `static/img/`
- User-customisable logo URL stored in `Profile.logo_url` (displayed in navbar if set)
