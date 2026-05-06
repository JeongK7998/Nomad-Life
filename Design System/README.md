# Wanted Design System

A reference design system extracted from Wanted — Korea's leading career & talent platform. The system covers all of Wanted's surfaces: the consumer career app (**Wanted**), the recruiting tool (**WantedSpace**), the freelance/contractor product (**WantedGigs**), the agent product (**WantedAgent**), and the embedded auth experience (**Wanted OneID**).

The system is built around restraint: a near-monochrome neutral palette, a single confident brand blue (`#0066FF`), the **Pretendard** family for type, and a tight 4-pt spatial grid. Most components are achromatic; color is deployed surgically — for primary CTAs, status, and brand moments — never decoratively.

---

## CONTENT FUNDAMENTALS

### What Wanted is
Wanted is a careers ecosystem: job discovery, applications, talent sourcing, recruiter workflows, freelance gigs, and AI-assisted matching. Every product in the family shares the same visual core but adapts density and chrome to its audience (consumers, recruiters, agencies).

### Voice & tone
- **Direct, calm, professional.** Sentences are short. Marketing copy is informational, not theatrical.
- **Korean-first** — copy is bilingual (Ko/En) but Korean is the primary language; never break Hangul lines mid-syllable.
- **Numbers earn trust** — Wanted leans on concrete stats (response rates, days-to-hire, salary medians). Use real numbers; do not invent stats to fill space.
- **No exclamation points** in product UI. Reserve them for promotional surfaces.

### Copy patterns
- Job titles: lead with role, then company, then location (`Senior Frontend Engineer · 토스 · 서울 강남구`).
- CTAs: imperative, 2–4 syllables in Korean, 1–3 words in English. (`지원하기`, `Apply`, `채용 보기`, `View jobs`.)
- Empty states: single sentence + a single primary action. No illustrations beyond a small symbol.

### Imagery
- Real photography: candid workplace shots, product screenshots, headshots — never stock people.
- Illustrations are **flat, geometric, monochrome-with-blue-accent**. Avoid gradients in illustration.
- Company logos are always shown on a neutral chip (`--background-alternative`) at consistent size.

---

## VISUAL FOUNDATIONS

### Type
**Pretendard** is the single typeface for all surfaces (Korean + Latin + JP coverage in the same family). The system defines **7 hierarchies × 18 styles** documented in `colors_and_type.css`:

| Hierarchy | Sizes | Use |
|---|---|---|
| Display | 56 / 40 / 36 | Hero & marketing only |
| Title   | 32 / 28 / 24 | Page titles, modal titles |
| Heading | 22 / 20 | Section headers |
| Headline| 18 / 17 | Card titles, list headers |
| Body    | 16 / 15 (normal + reading) | Paragraphs |
| Label   | 14 / 13 | Buttons, form labels, chips |
| Caption | 12 / 11 | Metadata, timestamps |

All sizes ship with explicit `letter-spacing` (negative for headings, positive for small text — Pretendard's metrics are tight at small sizes).

### Color
Tokens are split into **atomic** (named ramps `coolNeutral-99`…`coolNeutral-5`, `blue-99`…`blue-8`, plus accent ramps for red, green, orange, lime, cyan, lightBlue, violet, purple, pink) and **semantic** (e.g. `--label-normal`, `--background-alternative`, `--primary-normal`, `--status-positive`).

> **Rule of thumb:** in product code, always reference semantic tokens. Atomic tokens are only used inside the design system itself or for one-off marketing accents.

The same semantic names exist in **Light** (default) and **Dark** themes — switching themes flips one attribute (`data-theme="dark"`).

Status pairs:
- **Positive** — `#00BF40` (green-50)
- **Cautionary** — `#FF9200` (orange-50)
- **Negative** — `#FF4242` (red-50)

### Spacing & radius
4-pt grid: `2 / 4 / 6 / 8 / 10 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 / 96 / 128`.
Radius scale: `2 / 4 / 6 / 8 / 10 / 12 / 16 / 20 / 24 / 32 / full`.
Most controls land at **8px** radius; cards at **12–16px**; pills/avatars at `--radius-full`.

### Elevation
Five emphasized shadow levels (`xsmall` → `xlarge`). Wanted uses elevation sparingly — most cards rely on a 1px line (`--line-normal`) for separation, and shadows are reserved for popovers, dropdowns, and modals.

---

## ICONOGRAPHY

The system ships ~250 icons (24×24, 1.5–2px stroke equivalent, filled + outlined variants). They live in `assets/icons/`. A representative subset is curated in this kit; the full library follows the same naming convention (`name + variant` such as `bookmark.svg` / `bookmark-fill.svg`).

Categories:
- **Navigation:** home, search, bell, person, menu, close
- **Actions:** plus, minus, check, pencil, trash, copy, download, upload, share, refresh
- **Direction:** chevrons (up/down/left/right), arrows, more-horizontal, more-vertical
- **Status:** circle-check / circle-info / circle-exclamation / circle-close, triangle-exclamation
- **Domain:** business-bag, company, calendar, clock, location, star, bookmark, heart
- **Social:** Google, Apple, Kakao, Facebook, LinkedIn, X, YouTube, Instagram
- **Wanted nav family:** career, recruit, social, mypage, menu

All icons are designed to render at `currentColor` so they inherit the parent's text color cleanly across themes.

---

## BRAND & LOGOS

The Wanted mark is a stylized **W → arrow** glyph. The system includes:
- **Symbol** (square / circle backgrounds) — `assets/wanted-symbol.svg`
- **Horizontal logotype** — `Wanted`, `WantedGigs`, `WantedSpace`, `WantedAgent`, `Wanted LaaS`, `Wanted OneID`
- Colour variants: black, white, brand blue. Logos are recolored via `currentColor` on `<svg>` where possible.

Brand blue is **`#0066FF`** — used only for primary CTAs, brand moments, and the symbol. Avoid blue gradients; the brand reads at a single saturation.

---

## INDEX

- `colors_and_type.css` — all design tokens & type classes (light + dark)
- `fonts/` — Pretendard OTF (9 weights)
- `assets/` — logos
- `assets/icons/` — icon library
- Preview cards (load `done.html` to see all): typography, colors, spacing, components, brand
- UI kit pages — one per product surface
- `SKILL.md` — instructions for designers building with this system
