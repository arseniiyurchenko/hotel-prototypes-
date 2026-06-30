# Burtakas Hotel Homepage Prototype — Plan

Source: [https://www.burtakas.lv/](https://www.burtakas.lv/)

## Extracted content summary

| Field | Value |
|-------|-------|
| **Name** | Burtakas (Atpūtas komplekss Burtakas) |
| **Tagline** | Velnišķīgi laba atpūta |
| **Tier** | Mid-range / budget-friendly family recreation complex — warm, informal, negotiable “omulīgas cenas” |
| **Logo** | `https://www.burtakas.lv/themes/custom/burtakastheme/logo.gif` |
| **Brand colors** | Dark `#242232` / `#2d2b3a`, gold `#d4a574`, forest `#014923` / `#085959`, cream `#f9ecd8` |

### Location

Straupē, Straupes pagasts, Cēsu novads, Latvia (LV-4152). Landmarks/distances from site: Braslas upe, Burtakas iezis; 65 km Rīga, 25 km Cēsis, 25 km Sigulda, 35 km Valmiera, 34 km Limbaži.

### Room types (from /piedavajam)

1. **Lielpirts** — from €800 (whole building; sauna/kubls extra)
2. **Kubla pirts** — from €350 (2 bedrooms, up to 12 guests)
3. **Terases Brīvdienu māja** — €240–450 (2 bedrooms + studio; sauna, hidromasāžas SPA)
4. **Piestātnes mājiņas** — from €80 per cabin (3 camping cabins, warm season)
5. **BB pirts** — from €450 (5 bedrooms, hunter-style)

*Note: Site lists building/stay prices in EUR, not per-night hotel rates. Prototype shows “from €X” with source attribution.*

### Amenities (from homepage + Par mums)

Pirts/sauna, dīķi (ponds), seņču kubls, ūdenskritums, laivu braucieni pa Braslu, sporta laukumi, biljards/galda teniss/novuss, šahs/domino, ugunskurs, makšķerēšana, ēdināšana, bērnu izklaides (Tarzānu trase, Pirātu kuģis, u.c.), kāzas/sporta spēles.

**Not on site:** breakfast, parking policy, pet policy, star ratings — use neutral placeholders where needed.

### Image URLs (verified HTTP 200)

- Hero: `…/2026-01/front.jpg.webp`
- Lielpirts: `…/IMG_0655_1.jpg.webp`
- Kubla pirts: `…/k8.jpg.webp`
- Terases: `…/P8203025.jpg.webp`
- Piestātnes: `…/m3.jpg.webp`
- Aerial/complex: `…/skycam-41.jpg.webp`, `…/kop6.jpg.webp`

## Prototype sections

1. Hero — front photo, name, tagline, CTA
2. Booking widget — dates, guests, accommodation selector (UI only)
3. Room showcase — 5 real offerings as cards with EUR pricing
4. Amenities grid — icons for verified amenities only
5. Photo gallery — 6 hotlinked images
6. Location — Straupē + distances + static map placeholder
7. Trust strip — placeholder testimonials (no rating on source site)
8. Footer — real contact info + nav

## Design direction

Upgrade from current Drupal site: cleaner layout, stronger typography (Comfortaa + Overpass from source), warm cream/forest palette matching brand, fully responsive, production-ready polish appropriate for mid-range family recreation.

## Verification

- Playwright: image load check, booking widget interaction, desktop + mobile scroll
- Record walkthrough video to `/opt/cursor/artifacts/`
