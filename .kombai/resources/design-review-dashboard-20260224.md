# Design Review Results: Web Dashboard (/)

**Review Date**: 2026-02-24  
**Route**: `/` → `frontend_dashboard.html` (served by FastAPI)  
**Focus Areas**: Visual Design · UX/Usability · Responsive/Mobile · Accessibility · Micro-interactions · Consistency · Performance

---

## Summary

The dashboard has a clean, functional layout with a solid green brand colour and a clear two-column structure. However it has **critical accessibility failures** (no label associations on inputs, insufficient button colour contrast, dead nav links), several responsive breakpoint gaps on mobile (hidden nav with no fallback, sidebar input truncation), and uses Tailwind via CDN which is not suitable for production. There are also minor consistency issues in the heading hierarchy and card markup.

---

## Issues

| # | Issue | Criticality | Category | Location |
|---|-------|-------------|----------|----------|
| 1 | **No `for` attribute on form labels** — all 7 input labels are missing `for="input-*"`, breaking screen-reader label association | 🔴 Critical | Accessibility | `frontend_dashboard.html:41-82` |
| 2 | **Button colour contrast fails WCAG AA** — `emerald-600` (#059669) on white = ~3.76:1 (needs 4.5:1 for normal text) | 🔴 Critical | Accessibility | `frontend_dashboard.html:83` |
| 3 | **`alert()` used for form validation** — browser `alert()` blocks the UI, traps screen reader focus, and is inaccessible on mobile | 🔴 Critical | Accessibility / UX | `frontend_dashboard.html:149-151` |
| 4 | **All nav links are dead (`href="#"`)** — Suche, Favoriten, Wetter navigate nowhere; screen readers announce them as links but they do nothing | 🔴 Critical | UX / Accessibility | `frontend_dashboard.html:24-27` |
| 5 | **Nav hidden on mobile with no hamburger fallback** — `hidden md:flex` hides nav on mobile but provides zero alternative navigation | 🟠 High | Responsive | `frontend_dashboard.html:23` |
| 6 | **Sidebar input truncates text on desktop** — `input-cities` value "Amsterdam, Zandvoort, Rotterdam" clips at the narrow 1/4-width sidebar (`w-1/4`); no `title` tooltip | 🟠 High | Responsive / UX | `frontend_dashboard.html:42` |
| 7 | **Missing `aria-label` on search button** — button text changes dynamically to "Suche läuft…" but no `aria-live` or `aria-busy` is set during loading | 🟠 High | Accessibility | `frontend_dashboard.html:83, 155-156` |
| 8 | **`budget-type` select has no accessible label** — the `<select>` has `id="input-budget-type"` but no associated `<label>` and no `aria-label` | 🟠 High | Accessibility | `frontend_dashboard.html:75-78` |
| 9 | **Heading hierarchy broken** — page has one `<h1>` (nav brand), one page-level `<h2>` ("Deine Urlaubs-Deals"), but section titles "Airbnb Empfehlungen" and "Booking.com Favoriten" are also `<h2>` rather than `<h3>`, creating a flat/incorrect outline | 🟠 High | Accessibility / Consistency | `frontend_dashboard.html:98-100, 111-113` |
| 10 | **No skip-to-content link** — keyboard users must tab through the entire navbar before reaching any form field | 🟠 High | Accessibility | `frontend_dashboard.html:17-29` |
| 11 | **`via.placeholder.com` fallback is deprecated** — used in `onerror` handler and server-side fallback; service is unreliable and may break | 🟠 High | Performance / UX | `frontend_dashboard.html:193`, `api.py:84` |
| 12 | **Tailwind loaded via CDN** — `<script src="https://cdn.tailwindcss.com">` generates all ~3 MB of utility classes at runtime; unacceptable for production (slow, no tree-shaking) | 🟠 High | Performance | `frontend_dashboard.html:7` |
| 13 | **No keyboard focus indicator on nav links** — hover uses `hover:text-emerald-200` but there is no `focus-visible` style, leaving keyboard users without a visible focus ring | 🟡 Medium | Accessibility | `frontend_dashboard.html:24-27` |
| 14 | **Date inputs overflow on narrow sidebar** — calendar picker icon bleeds over the visible text area in the `grid-cols-2` date pair on small desktop widths | 🟡 Medium | Responsive | `frontend_dashboard.html:45-53` |
| 15 | **Empty state is not actionable** — both sections show just a search icon + "Noch keine Suche gestartet." with no call-to-action or instructional text | 🟡 Medium | UX | `frontend_dashboard.html:103-107, 116-121` |
| 16 | **`text-md` is not a valid Tailwind class** — deal card title uses `class="text-md font-bold"` which has no effect (correct class is `text-base`) | 🟡 Medium | Consistency | `frontend_dashboard.html:205` |
| 17 | **`text-[10px]` used in card instead of design token** — two price labels use arbitrary pixel values instead of a named size token | 🟡 Medium | Consistency | `frontend_dashboard.html:211, 216` |
| 18 | **No sort / filter controls on deal results** — after a search, users cannot re-sort by price, rating, or score without re-running the search | 🟡 Medium | UX | `frontend_dashboard.html:89-123` |
| 19 | **No favourite-save action on deal cards** — cards show a "Zum Angebot" link but have no way to save a deal to favourites from the dashboard | 🟡 Medium | UX | `frontend_dashboard.html:189-227` |
| 20 | **`deal-card` hover transition missing `will-change`** — `transform: translateY(-5px)` triggers layout recalculation; adding `will-change: transform` improves GPU compositing | 🟡 Medium | Micro-interactions | `frontend_dashboard.html:12` |
| 21 | **Budget-type `<select>` styling inconsistent** — uses `border-none bg-transparent` with `text-emerald-600 font-bold` and appears visually detached from the rest of the form | 🟡 Medium | Visual Design | `frontend_dashboard.html:75-78` |
| 22 | **Missing `loading="lazy"` on deal card images** — all listing images load eagerly even when off-screen; impacts page performance after a search | ⚪ Low | Performance | `frontend_dashboard.html:192-195` |
| 23 | **Missing favicon** — `GET /favicon.ico` returns 404, causing a console error on every page load | ⚪ Low | Visual Design | `api.py` (static files not configured) |
| 24 | **Footer missing `role="contentinfo"`** — while `<footer>` has implicit landmark role in HTML5, older screen readers benefit from explicit role | ⚪ Low | Accessibility | `frontend_dashboard.html:127` |
| 25 | **Sidebar `aside` missing `aria-label`** — the aside landmark has no accessible name; screen readers announce it simply as "complementary" | ⚪ Low | Accessibility | `frontend_dashboard.html:34` |
| 26 | **No transition on disabled search button** — button background colour change when disabled (`:disabled`) is abrupt; a short `transition` would feel more polished | ⚪ Low | Micro-interactions | `frontend_dashboard.html:83` |
| 27 | **No `rel="noopener"` on external deal links** — `target="_blank"` links include `rel="noreferrer"` (good) but missing `noopener` explicitly (though `noreferrer` implies it) | ⚪ Low | Performance / Security | `frontend_dashboard.html:221` |

---

## Criticality Legend
- 🔴 **Critical**: Breaks functionality or violates accessibility standards
- 🟠 **High**: Significantly impacts user experience or design quality
- 🟡 **Medium**: Noticeable issue that should be addressed
- ⚪ **Low**: Nice-to-have improvement

---

## Next Steps (Recommended Priority Order)

1. **Fix label associations** — add `for="input-*"` to every `<label>` (Issue #1) — 10 min
2. **Fix button colour contrast** — change `emerald-600` → `emerald-700` (`#047857`) on the CTA button and nav links (Issue #2) — 5 min
3. **Replace `alert()` with inline validation** — show error messages below fields using a `<p role="alert">` (Issue #3) — 30 min
4. **Implement real nav routes or remove links** — add `#suche`, `#favoriten` anchors or wire up actual pages (Issue #4) — 30 min
5. **Add hamburger menu for mobile** — reveal nav links in a drawer/dropdown on `md:hidden` screens (Issue #5) — 45 min
6. **Add skip-to-content link** — one hidden `<a href="#main-content">` at the top of `<body>` (Issue #10) — 10 min
7. **Fix heading hierarchy** — make section titles `<h3>` (Issue #9) — 5 min
8. **Add `aria-label` to search button and `aria-busy` during loading** — (Issues #7, #8) — 15 min
9. **Move to a proper Tailwind build** — set up Vite + Tailwind v3 via `npm` for production (Issue #12) — 2 hrs
10. **Replace `via.placeholder.com`** — use a self-hosted fallback or `picsum.photos` (Issue #11) — 15 min
11. **Add sort controls and favourite button to cards** — (Issues #18, #19) — 1–2 hrs
12. **Add `loading="lazy"` to deal card images** — (Issue #22) — 5 min

---

*Generated by Kombai Design Review · Route: `/` · 2026-02-24*
