# Hotel SPA Arkadia Homepage Prototype — Plan

Source: [https://www.hotelarkadia.lv](https://www.hotelarkadia.lv) (fetched live 2026-07-23)

## Extracted content summary

| Field | Value |
|-------|-------|
| **Property name** | Hotel SPA Arkadia / Hotel Arkadia (site title: HOTEL ARKADIA) |
| **Tagline (LV)** | *Laipni lūgti Hotel Arkadia* — Mierpilnā atpūtas oāze ikdienas steigas vidū, viesnīca atrodas tālāk no ikdienas burzmas — tuvu jūrai un priežu mežam, kur valda miers, svaigs gaiss un nesteidzīga atmosfēra. |
| **Tagline (EN)** | Welcome to Hotel Arkadia — Peaceful oasis away from the rush of everyday life… close to the sea and surrounded by pine forests… |
| **Logo** | `https://www.hotelarkadia.lv/image/catalog/arkadia/arkadia_logo.svg` (navy wordmark ≈ `#254991`) |
| **Brand colors (CSS)** | Primary coral `#e45858`, gold `#c9a84c`, dark `#1a1a2e`, cream `#f5f0e8` |
| **Tier** | **Mid-range** family / SPA / events hotel (≈ €60–100/night, conference + banquet booking flows, not boutique luxury) |

### Location (on site)

- **Apšuciems P128, Engures pagasts, LV-3113**
- Landmark language on homepage: **near the sea (jūra)** and **pine forest (priežu mežs)**
- Contact map embed: `57.0564848, 23.3126483`
- Phone: **+371 29132765** (also **+371 63143130** in house rules)
- Email: **mail@hotelarkadia.lv**
- Contact hours: **09:00–21:00**; check-in from **15:00**, check-out by **12:00** (house rules)

**Not named on the live site:** Lake Engure, Engure Nature Park, “Gulf of Riga” as a phrase, beach access claim. Prototype location copy uses only Apšuciems / Engures pagasts / sea / pine forest.

### Room types (from `/rezervacija`)

| Type | Size | From EUR/night | Photo on site |
|------|------|----------------|---------------|
| Divvietīgs numurs | 18 m² | **70** | placeholder only |
| Klasiskais Twin | 24 m² | **60** | twin-st-1 |
| Twin ar balkonu | 24 m² | **70** | twin-balcony-1 |
| Trīsvietīgs | 28 m² | **80** | triple-st-1 |
| Ģimenes numurs | 40 m² | sold out / **no price shown** → placeholder | family-1 |
| Lukss numurs | 55 m² | **100** | placeholder only |
| Triple ar terasi | — | **90** | placeholder only |

Included across rooms (site labels): TV, Wi-Fi, kettle, shower/WC (Lukss: large double bath), parking, children’s playroom visit; balcony on Twin ar balkonu / Triple ar terasi.

### Amenities verified on site

Parking, Wi-Fi, children’s playroom, conference halls, banquet / events, balcony/terrace (selected rooms), pets allowed with prior arrangement (€20 / €30 per night by size — house rules), sea & pine-forest setting.

**Not listed as facilities on scraped pages:** spa pool / sauna / jacuzzi details, grill, kitchen, ratings/reviews. Brand name includes “SPA”; amenities grid will not invent spa hardware.

### Image URLs (HTTP 200 verified)

1. Hero/exterior: `…/image/cache/catalog/arkadia/building-1920x1080.jpg`
2. Twin room: `…/image/catalog/arkadia/rooms/twin-st-1.jpeg`
3. Twin + balcony: `…/image/catalog/arkadia/rooms/twin-balcony-1.jpeg`
4. Triple: `…/image/catalog/arkadia/rooms/triple-st-1.jpeg`
5. Family: `…/image/catalog/arkadia/rooms/family-1.jpeg`
6. Venue / common: `…/image/cache/catalog/arkadia/venue/venue-001-800x600.jpg` (+ venue-002)

No dedicated beach / nature / spa feature photos found in the live catalog.

## Design direction

Clean mid-range seaside upgrade: logo navy + soft coastal sand/seafoam, coral CTA from brand primary, Cormorant Garamond + Source Sans 3. Sticky header with 32–48px side padding; smooth in-page anchors; UI-only booking widget.
