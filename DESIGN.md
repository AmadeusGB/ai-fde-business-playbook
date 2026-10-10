---
name: "Bringing AI into Business Operations"
description: "The published book’s forest green and cream identity extended for bilingual reading."
colors:
  paper: "#faf8f2"
  surface: "#f1eee5"
  ink: "#263b34"
  muted: "#59675f"
  line: "#d4dbd1"
  green: "#24443b"
  selected: "#e1eade"
  focus: "#8c4b26"
  dark-paper: "#17231e"
  dark-surface: "#202e27"
  dark-ink: "#e7ebe1"
  dark-muted: "#b1bcaf"
  dark-line: "#415146"
  dark-green: "#bfd5b4"
  dark-selected: "#314537"
  dark-focus: "#e3b48b"
typography:
  display:
    fontFamily: "Georgia, \"Songti SC\", \"Noto Serif CJK SC\", \"Source Han Serif SC\", serif"
    fontSize: "clamp(2.5rem, 5vw, 4.5rem)"
    fontWeight: 600
    lineHeight: 1.2
  headline:
    fontFamily: "Georgia, \"Songti SC\", \"Noto Serif CJK SC\", \"Source Han Serif SC\", serif"
    fontSize: "clamp(2rem, 3.1vw, 3rem)"
    fontWeight: 600
    lineHeight: 1.36
  body:
    fontFamily: "Georgia, \"Songti SC\", \"Noto Serif CJK SC\", \"Source Han Serif SC\", serif"
    fontSize: "1.13rem"
    fontWeight: 400
    lineHeight: 1.9
  navigation:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", sans-serif"
    fontSize: ".85rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  control: "5px"
  theme-control: "6px"
spacing:
  search-gap: ".6rem"
  edition-gap: ".8rem"
components:
  read-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: ".85rem 1.25rem"
  read-secondary:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.green}"
    rounded: "{rounded.control}"
    padding: ".85rem 1.25rem"
  search-input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: ".8rem"
  chapter-navigation:
    typography: "{typography.navigation}"
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    padding: ".48rem .65rem"
  section-index:
    padding: "1.1rem 0"
  reading-table:
    width: "100%"
---

# Design System: Bringing AI into Business Operations

## Overview

**Creative North Star: "The Published Book on Cream Paper"**

The published book is the visual authority. Forest green type, cream paper and the supplied illustrated cover carry its identity into a quiet bilingual reading environment. This is a code-led extension of that identity; no approved visual comp is asserted.

Serif book text occupies generous reading space while compact sans-serif navigation supports movement between editions, chapters and worksheets. The cover supplies illustration and material character; interface surfaces remain restrained.

**Key Characteristics:**

- Forest green and cream inherited from the cover.
- Serif reading paired with compact sans-serif navigation.
- Flat reading surfaces with a single ambient cover shadow.

## Colors

The palette extends the cover’s forest green and warm paper with muted reading aids.

### Primary

- **Forest Green** (`green`): headings, links and primary reading actions.
- **Selected Leaf** (`selected`): current chapter, secondary edition action and search highlights.
- **Warm Focus** (`focus`): visible keyboard outline.

### Neutral

- **Cream Paper** (`paper`): page canvas and sticky header.
- **Warm Surface** (`surface`): quotations, table headers and navigation hover.
- **Reading Ink** (`ink`): body text.
- **Muted Ink** (`muted`): chapter context, captions and utility labels.
- **Paper Divider** (`line`): quiet structural borders.

Dark counterparts are the actual theme overrides, applied by explicit theme choice or the system preference. Figures retain their authored colors and white image backing.

## Typography

Book headings and prose use the local serif stack in the frontmatter; navigation, table text and captions use the local sans-serif stack. No remote font is required.

The landing display is larger than chapter headings. Prose headings use relative sizing: second-level headings (1.55em, line-height 1.45), third-level headings (1.18em, line-height 1.5). English prose uses line-height (1.8) and a maximum width (74ch). At the smallest breakpoint prose becomes (1.06rem, line-height 1.95), and second-level headings become (1.36em).

## Layout

The desktop reader is a centered grid with a chapter sidebar (275px) and a flexible content region, bounded at (1600px). The sidebar scrolls independently below the sticky header (76px). The reading column is bounded at (860px), widening to (900px) from (1700px). Desktop article gutters use `clamp(1.5rem, 4vw, 5rem)`.

At (960px) and below, the sidebar yields to a native disclosure menu in the header; header height becomes (66px). At (600px) and below, reading gutters become (1.2rem). The landing page uses cover and title columns within (1160px), then changes to a vertically stacked text-first composition at the smallest breakpoint. The bilingual titles and edition actions retain parity.

## Elevation & Depth

Reading surfaces use color and thin dividers rather than shadows. Only the supplied cover receives an ambient shadow (`8px 15px 30px rgb(0 0 0 / 12%)`). Sticky navigation communicates position through its border and opaque paper background.

## Shapes

Reading surfaces remain rectangular. Controls and selected navigation use the small control radius; the theme control has its separate radius. Quotations are flat tonal rectangles. No ornamental clipping is applied to authored artwork.

## Components

### Reading actions

Solid green primary and selected-leaf secondary links use identical padding and weight (600). Hover underlines the label. Global keyboard focus uses a two-pixel warm outline with a four-pixel offset.

### Chapter navigation

Compact sans-serif links have muted text at rest, surface-colored hover, and selected-leaf current state with green text and weight (600). Chapter numbers use tabular numerals. The same chapter hierarchy is available through the mobile header disclosure.

### Search field

Paper background, reading ink, thin divider border and small corners. Placeholder text uses muted ink at full opacity. The adjacent search action uses green and paper colors.

### Section index

A native disclosure bounded by horizontal dividers, with ordinary linked lists. It remains visually subordinate to the chapter heading.

### Figures and captions

Figures fill the available column while preserving aspect ratio and link to the full asset. Captions use muted sans-serif text (0.82em, line-height 1.65). Source fidelity governs artwork: provenance is the public repository’s `book/` source path and SHA-256 recorded in `website-build-manifest.json`; published copies must remain byte-identical. This includes the eight marked English PNGs and their existing steganography. Metadata embedding is prohibited on these immutable authored assets. No machine-specific paths are part of provenance.

### Reading tables

Tables use sans-serif tabular text (0.86em, line-height 1.65), left alignment, tonal headers and row dividers. Their minimum width (600px) belongs inside a horizontally scrollable container with a reading hint. Preserve cells and source structure.

### Page navigation

Previous and next chapter links form a pair separated from the article by a top divider. Each link is bounded to (47%) of the row, with secondary direction labels and right alignment for the next chapter.

## Do's and Don'ts

### Do:

- Do retain the supplied cover and authored diagrams unchanged.
- Do use the chapter index and reading column on desktop, and the header menu on mobile.
- Do keep wide tables horizontally scrollable inside the reading column.
- Do preserve equivalent Chinese and English reading affordances.

### Don’t:

- Don’t re-encode, annotate, resize on disk, recolor or embed metadata in shipping source PNG/SVG assets.
- Don’t force wide tables into the viewport by reducing reading text to illegible sizes.
- Don’t add external font dependencies.
