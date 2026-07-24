# Auchen Castle Homepage Prototype — Plan

Source: [https://www.auchencastle.co.uk/conferences](https://www.auchencastle.co.uk/conferences) (primary), plus related pages on the same site for branding, spaces, location, and images (fetched 24 July 2026).

## Extracted content summary

| Field | Value |
|-------|-------|
| **Name** | Auchen Castle |
| **Conferences heading** | “CONFERENCES at the Castle” |
| **Page title / positioning line** | “Business Events Venue on Scotland - England border” |
| **Supporting copy (conferences)** | “The perfect conference venue in the rolling hills of Dumfrieshire” — peaceful country estate on the Scotland–England border; tranquil castle + private grounds. |
| **Homepage wedding tagline (same brand)** | “A Unique Castle Wedding Venue” / “In south-west Scotland”; “Original Scottish Fairytale Castle” |
| **Collection** | Part of **The Original Collection** |
| **Tier** | **Premium** castle venue — site states “Five-star castle venue”; fairytale / exclusive-use presentation; polished photography; Original Collection membership. |
| **Logo** | `https://www.ocadmin.co.uk/images/websites/638028283061947044_auchencastle17708.png` (AUCHEN / CASTLE wordmark; white on transparent for taupe header). Secondary ident: `…/Auchenlogo37639.png` |
| **Brand colors (live CSS)** | Primary taupe `#BAAEA7`; menu/dark taupe `#A39892`; book CTA `#726B67` / hover `#544F4C`; soft border `#D8CBC3`; vouchers `#A09690`; body text `#424242`; white. Fonts referenced: Gill Sans MT, Mukta. |

### Location

**Auchen Castle**, Beattock, Near Moffat, Dumfriesshire DG10 9SH, Scotland.  
Tel: **01683 300407** · Email: **info@auchencastle.uk**

Nearby / access (from conferences, contact, weddings, explore pages):

- Dumfriesshire / Dumfries & Galloway; Moffat hills; Scotland–England border
- About an hour from Glasgow and Edinburgh; contact page also notes airports ~1 hour; weddings page: 30 minutes north of Gretna Green
- Just off the M74 (J15 from south / J16 from north); nearest rail Lockerbie (~20-minute taxi)
- Moffat town centre ~10 minutes by car

### Event / room space types (as labeled on site)

From **/conferences**:

- Two main **meeting rooms**
- Additional **breakout rooms**
- **34 acres of private grounds**
- Larger **events, dinners, ceremonies**, corporate events, product launches

From weddings / related pages (same venue):

- **Ceremony Room** (fireplace; garden views; outdoor option by Italianate fountain)
- **Grand ballroom** (wedding breakfast / after-party)
- **Reception rooms** / wedding room
- **Castle turrets** (elopements)
- **Italianate gardens** / landscaped gardens
- **Cosy bar**
- **26 en-suite bedrooms** (52 guests on weddings highlights)

### Amenities / features (verified)

- Conferences & meetings for **up to 100 delegates**
- **26 en-suite bedrooms**; Day Delegate overnight option includes single-occupancy B&B
- **Free Wi-Fi**
- **Parking for 30 cars**
- Catering within packages (tea/coffee + chef’s snack, buffet lunch, water with cordial; 24hr also three-course dinner)
- Stationery & sweets (in delegate packages)
- Team-building / outdoor pursuits: highland games, archery
- Whisky tastings and other activities on arrangement
- Conference team contact for coordination
- Weddings highlights also: expert manager & wedding planner; award-winning gins & whiskies in bar; majestic interior “bursting with history”; outdoor ceremonies; dining for 110 / dancing for 150

**Not explicitly listed on source (not fabricated):** dedicated AV / projector / PA kit inventory; star rating on the conferences page itself (five-star appears on weddings highlights); a photo labeled specifically as a “conference room” (conferences page shows exterior + Italianate gardens only).

### Pricing / packages (conferences page)

| Package | Price | Includes |
|---------|-------|----------|
| **Day Delegate** | **£45 per person** | 3× tea/coffee with chef’s snack; buffet lunch; water with cordial; stationery; sweets |
| **24 Hr Day Delegate** | **£220 per person** | Same as day + single occupancy bed & breakfast + three-course dinner |

### Image URLs used (HTTP 200 on source CDN)

| Role | URL | Site alt / label |
|------|-----|------------------|
| Logo | `…/websites/638028283061947044_auchencastle17708.png` | Auchen Castle |
| Hero / exterior + gardens | `…/photosv2/AuchenconferenceWW1500x90039787.jpg` | Front elevation of Auchen Castle and Italianate gardens |
| Grounds / aerial | `…/photosv2/home-main-1500x90057225.jpg` | Aerial shot of Auchen |
| Ceremony Room (event space) | `…/photosv2/Auchen_BethFaulder_553744989.jpg` | Room ready for guests (Ceremony Room setup; gallery94937.jpg on source has a baked-in “GALLERY” overlay, so unused) |
| Wedding reception room | `…/photosv2/wedding-strip-1500x50026888.jpg` | Auchen Castle wedding reception room |
| Historic staircase | `…/photosv2/Auchen_Mark_Keogh_10649279.jpg` | Bride descending stairs |
| Entrance / turret character | `…/photosv2/AUCHENTURRETSHOOT33875-1200x80088744.jpg` | Bride at the entrance to Auchen Castle |

**Note:** No image on the conferences page is labeled as a conference/meeting room interior — Ceremony Room and wedding reception room are the closest labeled event interiors on the live site.

## Prototype sections

1. Hero — full-bleed castle exterior; brand; conferences positioning line; short supporting sentence; CTA
2. Enquiry widget — date, delegate band, event type (UI only; mirrors conference contact intent)
3. Spaces — meeting rooms, breakout rooms, grounds, bedrooms as labeled
4. Features — verified amenities only; neutral note where AV kit is not listed
5. Delegate packages — £45 / £220 from conferences page
6. Gallery — real hotlinked venue photos
7. Location — Beattock / Moffat / Dumfriesshire + access notes from site
8. Contact footer — real address, phone, email

## Design direction

Premium Scottish castle: stone taupe brand palette from live CSS (`#BAAEA7` family) with deep slate charcoal; **Mukta** (referenced on live site) + expressive display serif; full-bleed hero; atmospheric stone/gradient backgrounds (not flat white, not cream/terracotta template); restrained motion (header state, hero drift, reveal).

## Verification

- Playwright: image load check, enquiry form interaction, desktop + mobile nav/screenshots
- Walkthrough video to `/opt/cursor/artifacts/`
