# Silazari — Logo & Dominant Brand Colors

Source: [https://silazari.lv/](https://silazari.lv/)  
Extracted: 2026-07-14

## Logo

| Variant | Role | URL | Notes |
|---------|------|-----|-------|
| **Primary (light)** | Hero / schema.org organization logo | `https://silazari.lv/wp-content/uploads/2024/01/Group-24.svg` | Wordmark + mark; fill `#F7E6DE` (for dark/photo backgrounds). ViewBox `842×398`. HTTP 200. |
| **Secondary (dark / full color)** | Hero carousel alternate | `https://silazari.lv/wp-content/uploads/2024/02/Silazari_Brand_secondary-logo-dark.svg` | Dark wordmark + illustrated pine/cabin mark using full palette. ViewBox `598×282`. HTTP 200. |
| **Footer / vertical** | Footer brand lockup | `https://silazari.lv/wp-content/uploads/2024/01/Group-13.svg` | Vertical mark; fills `#0D5B6D` + `#F7E6DE`. ViewBox `177×257`. HTTP 200. |
| **Favicon** | Browser icon | `https://silazari.lv/wp-content/uploads/2024/02/favicon.png` | HTTP 200. |

Site header uses an empty `.navbar-brand` anchor (no inline `<img>`); logos appear in the hero carousel and footer. Yoast JSON-LD sets organization logo to **Group-24.svg**.

## Dominant brand colors

Derived from live custom CSS (`#wp-custom-css`) and the secondary logo SVG style tokens.

| Token | Hex | Usage on live site |
|-------|-----|--------------------|
| **Ink / deep teal** | `#062830` | Body text, headings, footer background, reverse CTAs (`.silazarireverse`) |
| **Cream / blush** | `#F7E6DE` | Nav links, footer text, section wash (`.grey`), primary CTA (`.btnmatissblack`), light logo fill |
| **Coral / peach** | `#E7B49C` | Accent (e.g. jacuzzi table border); logo mark |
| **Seafoam** | `#85C1B0` | Logo mark accent |
| **Mint mist** | `#D5EAE4` | Divider (`.br-white`); logo mark |
| **Logo teal** | `#0D5B6D` | Footer / vertical logo fill |
| **Mid teal** | `#0B454F` | Logo stroke / secondary ink |
| **White** | `#FFFFFF` | Surfaces (`.bgwhite`), header glass |

### Prototype CSS variables (recommended)

```css
:root {
  --ink: #062830;
  --cream: #F7E6DE;
  --coral: #E7B49C;
  --seafoam: #85C1B0;
  --mint: #D5EAE4;
  --logo-teal: #0D5B6D;
  --mid-teal: #0B454F;
  --white: #FFFFFF;
}
```

### Typography (from source, for context)

- Body: Lexend / Lexend Deca  
- Display headings: Granville  

## Visual reference

Open `brand-reference.html` in this folder for hotlinked logos and color swatches.
