# Vendored highlight.js

This directory contains the minified static assets of
[highlight.js](https://highlightjs.org/) version 11.8.0, bundled with the
theme so that syntax highlighting works without any external CDN (offline,
intranet and privacy-sensitive builds included).

It mirrors the layout of the official CDN distribution:

* `highlight.min.js` — core library (includes the 23 common languages).
* `languages/*.min.js` — additional language packs, loaded via the
  `hljs_languages` theme config option.
* `styles/*.min.css` (and `styles/base16/*.min.css`) — all available styles,
  selected via the `hljs_style` theme config option.

## Upgrading

To update to a newer highlight.js release, replace the contents of this
directory with the corresponding files from the official CDN distribution
(e.g. <https://cdnjs.cloudflare.com/ajax/libs/highlight.js/VERSION/>) and keep
the layout unchanged. The BSD-3-Clause license of highlight.js is in
`LICENSE`.
