# Silazari Klapkalnciems Homepage Prototype — Plan

Source: [https://silazari.lv/](https://silazari.lv/)

## Extracted content summary

| Field | Value |
|-------|-------|
| **Name** | Silazari Klapkalnciems |
| **Tagline** | Ģimenes lolotas brīvdienu mājas priežu meža ielokā piejūrā (family holiday homes in the pine forest by the sea) — derived from site meta + destination copy |
| **Tier** | **Mid-range** — coastal family holiday homes; warm, practical, nature-led. Not budget camping; not boutique hotel |
| **Logo** | `https://silazari.lv/wp-content/uploads/2024/01/Group-24.svg` |
| **Brand colors** | Deep teal `#062830`, blush `#F7E6DE`, peach accent `#E7B49C`, soft mint `#D5EAE4`, white |

### Positioning rationale (tone + presentation)

See also repo root [`POSITIONING_TIERS.md`](../POSITIONING_TIERS.md).

1. **Tone:** Family-project hospitality (“kopts un lolots ģimenes projekts”), self-catering comfort, pine-forest calm. Jacuzzi copy is poetic but framed as a bookable extra, not a spa identity.
2. **Presentation:** Bootscore WordPress theme with custom Granville + Lexend Deca and teal/blush brand — polished mid-market, not editorial boutique or bare-bones budget.
3. **Offer shape:** Two whole houses (Lielā / Mazā Māja) with seasonal weekday/weekend EUR tables — transparent mid-range holiday-home merchandising.
4. **Counter-signals:** Reject **budget** (private jacuzzi houses, curated brand, €150–230/day). Reject **boutique** (no hotel service story; rate tables and informal family voice dominate).

### Location

“Silazari”, Klapkalnciems, Engures pagasts, Tukuma novads, LV-3113. ~7 min walk to Klapkalnciema pludmale via Lāčupītes dendrārijs. Nearby: Klapkalnciema Zivis, Ragaciems restaurants (Ribas, Bermudas).

### Accommodation (from homepage)

1. **Lielā Māja** — 53 m², up to 6 guests; 2 bedrooms + sofa bed; private jacuzzi on terrace; full kitchen, bathroom, AC, heating, coffee machine, terrace, grill, hammock, playground access. Summer from ~€160–230/day (seasonal).
2. **Mazā Māja** — 35 m², comfortable for ~4 (sleeps up to 6); 1 bedroom + loft + sofa bed; jacuzzi, kitchen, bathroom, AC, heating, terrace amenities. Summer from ~€150–220/day (seasonal).

Pricing notes on site: base for 4 guests; +€20 per extra guest; children under 8 free; holiday rates may differ. Jacuzzi add-on: €60–70/day.

### Amenities (verified on site)

Private jacuzzi/hot tub, fully equipped kitchen, AC, heating, coffee machine, terrace + outdoor furniture, grill, hammock, children’s playground, year-round stay, forest/sea access via dendrārijs path. Booking via WPForms enquiry (“Rezervēt” / “Rezervē šeit!”).

### Image / asset URLs (from live site)

- Logo: `…/2024/01/Group-24.svg`
- OG / brand photo: `…/2024/03/Silazari.jpg`
- Icon paths: `…/2024/01/Path-104.svg` … `Path-108.svg`, `Group-13.svg`

*(Gallery/room photo URLs should be verified HTTP 200 when building the page.)*

## Prototype sections

1. Hero — full-bleed coastal/forest photo, brand name hero-level, one headline, one supporting line, CTA (Rezervēt)
2. Booking / enquiry widget — dates, house selector, guests (UI only; source uses form enquiry)
3. Houses — Lielā + Mazā Māja with real specs and seasonal “from” pricing
4. Jacuzzi — lifestyle section with add-on rates
5. Amenities — verified comfort extras only
6. Apkārtnē — dendrārijs, beach, local food
7. Location + contact — address, phones, email
8. Footer — brand + nav

## Design direction (mid-range)

Upgrade Bootscore presentation: stronger brand-first hero, teal/blush/mint CSS variables, Granville-like display + Lexend/clean sans body, full-bleed photography, restrained motion (2–3 intentional). Keep transparent pricing and warm family tone — do **not** restyle as boutique hotel (no gold/navy chrome, no spa-resort overlay badges, no invented concierge copy).

## Verification

- Playwright: image load check, enquiry/booking UI interaction, desktop + mobile
- Walkthrough video to `/opt/cursor/artifacts/`
