# Szent Adalbert Event Center Homepage Prototype — Plan

Source: [https://www.szentadalbert.hu](https://www.szentadalbert.hu) (fetched 24 July 2026; content via `/hu/index.php/en/` and key HU/EN subpages)

## Extracted content summary

| Field | Value |
|-------|-------|
| **Name** | **Szent Adalbert Központ** (site nav / titles). English logo wordmark: **SZENT ADALBERT EVENT CENTER**. Meta description / brand phrasing: **Szent Adalbert Rendezvényközpont**; body copy: **The Szent Adalbert Event Center**. |
| **Tagline** | No single dedicated slogan string. Strongest repeated homepage marketing line: **“All in one place”** (rooms + accommodation + own catering + parking). Wedding homepage line: “Make your wedding vows where kings did the same!” Event page: “We realize your ideas!” Historic motto on façade: **“Pietati et scientiis”** — “for the piety and the sciences.” |
| **Tier** | **Premium / upper mid-premium historic venue** — neoclassical Old Seminary (József Hild, 1865); “elegant,” “high-quality,” banquet hall with crystal chandeliers; “exclusive Prímás Pince”; professional AV incl. simultaneous interpretation & hybrid conference; gold-on-dark logo. |
| **Logo** | EN: `https://www.szentadalbert.hu/hu/images/szentadalbertlogo-h-en.png` · HU: `…/szentadalbertlogo-h.png` (gold circular building seal + wordmark). |
| **Brand colors** | Template/accent gold `#d3a051` / `#d2a050` (also `#ac7a2b`, `#c08831`); logo gold ≈ `#c59c5f`; dark charcoal `#2d2d2d` / `#24252a`; white. Site typeface: **Domine**. |

### Location

**2500 Esztergom, Szent István tér 10.** (Contact page). Footer also lists **Szent István tér 11.** — site inconsistency; prototype uses Contact address and notes the footer variant.

Nearby / positioning from site: historic quarter of Esztergom, **embraced by the Basilica and the Danube**; Danube Bend; **≈40 km from Budapest**; Várhegy / Basilica area for Hotel Adalbert buildings.

Phone: **+36 33 541 900**. Sales: Diána Priegl · `priegl.diana@szentadalbert.hu` · +36 20 663 3582; Laura Gregóczki · `titkarsag@szentadalbert.hu` · +36 20 214 1729.

### Event / room space types (as labeled)

1. **Reception hall** (Fogadóterem) — small presentations, trainings, civil ceremonies; Ernő Jeges painting
2. **Banquet hall** (Díszterem) — most elegant; paintings & crystal chandeliers
3. **Szent István conference hall** — largest; divisible into three with soundproof walls
4. **Szent Adalbert restaurant** — terrace access; gatherings & weddings
5. **Auditorium** (Nagyelőadó) — fixed seating; lectures / smaller conferences
6. **Classroom** (Tanterem) — several rooms; small-group training
7. **Mindszenty event hall** — exhibitions, team building, conferences, plays, art openings
8. **Library** — Theological College library (special venue)
9. **Chapel** — masses / church ceremonies
10. **Inner court** & **ornamental garden** — outdoor ceremonies / receptions
11. Additional: **Prímás Pince** and **Hotel Adalbert** (linked sister venues)

Homepage also: larger halls for conferences; smaller section halls ideal for **30–50 people**; complex capacity **up to 800 guests**.

### Amenities / features (verified on source)

- Own parking lot — up to **150 vehicles**
- Own catering / kitchen (coffee breaks through gala / wedding dinners); self-serving restaurant; Prímás Pince à la carte
- Technical equipment: projector & screen, sound & microphones, ventilation/heating/cooling, Wi-Fi, teleconferencing, hybrid conference, simultaneous interpretation, flip chart
- Natural light with darkening option
- Own furniture / versatile furnishing
- Discount for children
- Accessibility via elevator for physically disabled
- Professional in-house event planning (planning → organization → implementation)
- Accommodation via **Hotel Adalbert** (two properties; bridal party up to **150** guests; wedding breakfast buffet)

### Pricing / packages

**No published numeric venue hire or wedding package prices** on reviewed pages. CTA pattern: **Requests for quotations**. Promotional: **“2026 Wedding Sale — 2027 Weddings at this year’s prices. Valid until April 30, 2026.”** Catering takeaway note (not venue hire): foam tray **600 Ft/db**. Prototype uses inquiry CTA only — no invented prices.

### Image URLs used (HTTP 200)

| Role | URL |
|------|-----|
| Logo | `…/hu/images/szentadalbertlogo-h-en.png` |
| Hero / exterior (courtyard through arch) | `…/com_osgallery/gal-1/original/szakhomlok00264E6271A-FA9C-2EFE-3F42-CFE10C64849D.jpg` |
| Conference hall | `…/images/slideszak/slideszak02x.jpg` |
| Wedding / banquet setup | `…/images/slideszak/slideszak03.jpg` |
| Night courtyard wedding (standout) | `…/images/red/esk-esti01_resize.jpg` |
| Lobby / historic interior | `…/images/slideszak/slideszak01.jpg` |
| Catering buffet | `…/images/red/konf_catering3_resize.jpg` |
| Garden / grounds at night | `…/images/red/Hotel_040_resize.jpg` |

**Missing on source (not fabricated):** fixed HUF/EUR package price list; star ratings / aggregate review score on homepage; a single official short English slogan beyond the lines above; consistent street number (10 vs 11).

## Prototype sections

1. Hero — full-bleed exterior; brand; “All in one place”; one supporting sentence; CTA
2. Inquiry widget — event date, guest band, event type (UI only → quotation)
3. Spaces — labeled halls from the Event page
4. Amenities — verified features only
5. Weddings — copy + sale note without invented prices
6. Gallery — real hotlinked photos
7. Location — Esztergom + Basilica / Danube / Budapest 40 km
8. Footer — real phones, emails, address from Contact

## Design direction

Premium historic venue: Domine (source) + distinctive sans; charcoal + site gold `#d3a051`; cool limestone paper (avoid cream/terracotta AI cliché and purple gradients); full-bleed hero; restrained motion (header, reveal, subtle hero scale).

## Verification

- Playwright: image load check, inquiry widget interaction, desktop + mobile
- Walkthrough video to `/opt/cursor/artifacts/`
