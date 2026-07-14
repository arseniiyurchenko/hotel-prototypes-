# Silazari Klapkalnciems Homepage Prototype — Plan

Source: [https://silazari.lv/](https://silazari.lv/)

## Conditional pricing rule

**Rule:** Show EUR pricing in the prototype **only if** the live site publishes rates. Do not invent prices.

| Check | Result |
|-------|--------|
| Pricing published on silazari.lv? | **Yes** — summer rate tables for both houses + jacuzzi |
| Prototype action | Display real “from €X / day” rates + seasonal tables + site footnotes |

If a future property has no published rates, use a labeled placeholder (e.g. `Cena pēc pieprasījuma (nav norādīta vietnē)`) instead of fabricating numbers — same pattern as Saules kempings / Mētras Māja.

## Extracted pricing (silazari.lv)

Base: **4 guests**. Each additional guest **+ €20**. Children under 8 not counted. Holiday periods may differ.

### Lielā Māja (53 m², up to 6)

| Month | Weekday / Sunday | Friday | Saturday |
|-------|------------------|--------|----------|
| June | €160/day | €190 | €210 |
| July | €180/day | €220 | €230 |
| August | €170/day | €200 | €220 |

**Prototype “from” price:** €160 / day (June weekday floor).

### Mazā Māja (35 m², up to 6)

| Month | Sun–Thu | Friday | Saturday |
|-------|---------|--------|----------|
| June | €150/day | €180 | €200 |
| July | €170/day | €210 | €220 |
| August | €165/day | €190 | €210 |

**Prototype “from” price:** €150 / day (June Sun–Thu floor).

### Džakuzi masāžas kubls

| Days | Rate |
|------|------|
| Mon–Thu, Sunday | €60/day |
| Friday, Saturday | €70/day |

## Other extracted content

| Field | Value |
|-------|-------|
| **Name** | Silazari Klapkalnciems |
| **Tagline** | Ģimenes atpūtas mājas piejūrā — Klapkalnciems |
| **Tier** | Mid-range coastal holiday houses (private jacuzzi, full kitchen) |
| **Logo** | `https://silazari.lv/wp-content/uploads/2024/01/Group-24.svg` |
| **Brand colors** | Deep teal `#062830`, sand `#F7E6DE`, coral `#E7B49C` |
| **Fonts (site)** | Lexend + Granville → prototype uses Lexend + Fraunces |
| **Phone** | +371 20330956, +371 28304413 |
| **Email** | silazarihome@gmail.com |
| **Location** | Silazari, Klapkalnciems, Engures pag., Tukuma nov., LV-3113 |

### Image URLs (HTTP 200)

- Hero / outside: `…/2024/01/silazari-outside.webp`, `…/2024/01/background.webp`
- Houses: `…/2024/01/big2x.webp`, `…/2024/01/small2x.webp`
- Gallery: `…/2024/02/Photo1–5-scaled.jpg`, beach, forest, restaurant, jacuzzi

## Prototype sections

1. Hero — full-bleed coastal image, brand, CTA
2. Booking widget — dates, guests, house selector (UI only)
3. Houses + **published pricing** (from rates + seasonal tables)
4. Jacuzzi add-on with published €60–70 rates
5. Amenities (source-verified)
6. Gallery (hotlinked)
7. Location — Klapkalnciems + Lāčupītes dendrārijs
8. Trust / footer — real contact
