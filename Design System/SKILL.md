# SKILL.md — Designing with the Wanted Design System

You are designing for a product in the **Wanted** family (Wanted, WantedSpace, WantedGigs, WantedAgent, Wanted OneID, Wanted LaaS). This skill captures the do's and don'ts so your output looks like Wanted, not like a generic SaaS dashboard.

## Always start here
1. Link `colors_and_type.css` from the project root: `<link rel="stylesheet" href="colors_and_type.css">`. This installs the **Pretendard** family, every color token, the type scale, radii, shadows, and spacing.
2. Reach for **semantic tokens** first (`--label-normal`, `--background-alternative`, `--primary-normal`, `--status-positive`). Only fall back to atomic tokens (`--color-coolNeutral-22`, `--color-blue-40`) for one-off marketing accents.
3. Set the locale: Wanted is Korean-first. Use `lang="ko"` on the root and write headings in Korean with optional English secondary.

## Type
- Use the `t-*` classes (e.g. `class="t-title2"`) — they bake size, line-height and letter-spacing.
- Headings are **700 (Bold)**; body and labels are **500 (Medium)**. Don't go lighter than 500 on UI text.
- Korean: never break Hangul mid-syllable. Add `text-wrap: pretty;` to long headings.
- Numbers: add `font-variant-numeric: tabular-nums;` anywhere a count, %, money or date appears.

## Color
- **One blue.** Brand blue (`#0066FF`) is for primary CTAs, the brand mark, and brand moments. Never use blue for decoration, gradients, or backgrounds.
- **Greys do the work.** 90% of any Wanted screen is `coolNeutral-99 → coolNeutral-10`. Use `--background-alternative` (#F7F7F8) for "card on card" depth before reaching for a shadow.
- **Status is rare.** A red dot on a notification, a green pill on "합격" — that's it. Never paint whole rows red or green.
- **Dark mode** is `<body data-theme="dark">`. Test it; the semantic tokens already flip.

## Layout
- 4-pt grid. Use `var(--space-N)`. Most card padding is **20–24px**, gap inside cards **12–14px**.
- Card radius: **12px** (compact) or **16px** (hero). Pills/avatars: `--radius-full`.
- Border before shadow. Wanted prefers a 1px `--line-neutral` outline over elevation. Reserve shadows for popovers/dropdowns/modals.
- Sidebar nav (recruiter products): dark `coolNeutral-10`, blue active highlight with a 3px left border.

## Voice & copy
- Imperative CTAs: `지원하기`, `Apply`, `채용 보기`. 2–4 syllables in Korean, 1–3 words in English.
- Numbers earn trust. Use real-feeling stats (`평균 응답 2.3일`, `합격축하금 1,500,000원`) — not invented ones.
- No exclamation points in product UI. No emoji unless the surface explicitly opts in.
- Job title → company → location, in that order, on every job card.

## Iconography
- All icons live in `assets/icons/` at 24×24, designed for `currentColor`. Sized via `width`/`height` (typically 18, 20, 22, 24).
- Filled vs. outline: filled (`-fill.svg`) for **active state**, outline for default. Bottom-nav active tab uses fill.
- Don't draw your own icon — use a placeholder and ask the user.

## Brand
- The Wanted symbol is a stylized W → arrow. Available colors: black, white, brand blue. Nothing else.
- Wordmarks for the product family: `wanted-logotype.svg`, `wanted-gigs-logotype.svg`, `wanted-space-logotype.svg`, `wanted-agent-logotype.svg`, `wanted-laas-logotype.svg`, `wanted-oneid.svg`. Recolor via `filter: brightness(0) invert(1)` for white on dark.
- Clearspace ≥ symbol height around any logo. No outlines, gradients, or rotations on the mark.

## Components — quick recipes
- **Primary button**: `background: var(--primary-normal); color: #fff; height: 40-48px; border-radius: 8px; font-weight: 600;`
- **Secondary**: dark — `background: var(--coolNeutral-10); color: #fff;` or outline — `background: transparent; box-shadow: inset 0 0 0 1px var(--line-normal);`
- **Job card**: white surface, 1px neutral border, hover → border darkens to `--label-normal` + 2px translateY + xsmall shadow.
- **Filter chip**: 36px tall, `border-radius: 9999px`. Active = `coolNeutral-10` + white text. Default = white + 1px line.
- **Badge**: 18–22px tall, 4px radius, 11–12px font, 700 weight. Tints at 10% opacity of their semantic color.

## What NOT to do
- ❌ Gradients on text, buttons, or large surfaces (the dark blue marketing hero is the *one* exception).
- ❌ Multiple competing accent colors. Pick one signal color per surface.
- ❌ Soft drop-shadows on every card (the system reads flat — earn elevation).
- ❌ "Inter" or "Roboto" fallback fonts. Pretendard or nothing.
- ❌ Filling space with placeholder text or invented stats. Less is more.

## Reference
- `previews/type.html` — full type scale with Korean specimens
- `previews/colors.html` — atomic + semantic tokens, light/dark
- `previews/spacing.html` — 4-pt grid, radii, shadows
- `previews/components.html` — buttons, inputs, cards, badges, alerts
- `previews/brand.html` — logos, symbol, do/don't
- `ui-kits/wanted-consumer.html` — career discovery (desktop)
- `ui-kits/wanted-space.html` — recruiter pipeline (desktop)
- `ui-kits/wanted-agent-mobile.html` — agent app (iOS)
