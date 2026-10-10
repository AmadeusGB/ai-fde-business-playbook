# Bilingual online book

The author approved a GitHub Pages site containing both editions, with a language choice, chapter navigation, figures, tables and existing downloads. The design extends the published book cover's identity rather than the reference website's layout.

Generate a separate static page for each chapter and worksheet, plus reading guide, author and rights pages. The landing page opens either edition. URLs use matching chapter numbers so a language switch can take readers to the same chapter. Page headings have shareable anchors. Search runs locally over a language-specific index loaded only on the search page.

Use the existing source files without rewriting or reassembling the book. Chinese diagrams use the published PNGs; English diagrams use SVG except the eight marked PNGs. Images load lazily and open at original size. Tables scroll horizontally within their reading column. The website copies only content it needs; production records, secrets and review artifacts are excluded.

GitHub Actions installs pinned generator dependencies, builds and checks local links and source coverage, then publishes only the generated output to Pages. The Chinese and English downloadable documents remain their existing versions. Verify desktop and mobile navigation, images, tables, language switching, search, dark mode, all source mappings and marked PNG hashes before deployment.
