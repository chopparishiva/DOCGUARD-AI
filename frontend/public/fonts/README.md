# Supplied font files — drop-in location

DocGuard AI renders with:

- **Inter** — primary sans (weights 300–700), loaded from Google Fonts in `index.html`.
- **Instrument Serif** — italic serif accent used for the AI/product phrase, loaded from Google Fonts in `index.html`.

The frontend spec specifies the exact supplied font files. Those files were not
present in the workspace, so we fall back to the Google-hosted editions of the
*same families* (satisfying "do not substitute fonts unless the exact supplied
font files are unavailable").

## If you obtain the exact supplied font files

1. Place them here, e.g.:
   - `InstrumentSerif-Italic.woff2` / `.woff`
2. Open `src/styles/global.css` and uncomment the matching `@font-face` block so
   the local definition takes precedence over the hosted font.
3. Rebuild (`npm run build`).

Do **not** enable a `@font-face` block while its file is missing — a broken
`src` shadows the hosted fallback and the family would silently drop to the
generic `serif` stack.