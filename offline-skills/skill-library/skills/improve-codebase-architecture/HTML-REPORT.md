# Offline HTML architecture report

Use one self-contained HTML file. All styles are inline; diagrams are inline SVG
or semantic HTML. Do not load Tailwind, Mermaid, fonts or images from a CDN.
Preserve the upstream report's purpose: candidate, files, problem, change,
benefit, before/after and recommendation. Include an ADR conflict when relevant.

```html
<!doctype html>
<html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Architecture review</title>
<style>
body{font:16px/1.6 system-ui,sans-serif;margin:0;color:#172b42;background:#f5f7fa}
main{max-width:1050px;margin:auto;padding:24px}article{background:white;border:1px solid #ccd5df;border-radius:8px;padding:20px;margin:20px 0}
.comparison{display:grid;grid-template-columns:1fr 1fr;gap:16px}svg{max-width:100%;height:auto}code{overflow-wrap:anywhere}
@media(max-width:650px){.comparison{grid-template-columns:1fr}}
</style>
<main><h1>Architecture review</h1>
<article><h2>Candidate title</h2><p>Recommendation and affected files.</p>
<div class="comparison"><section><h3>Before</h3>
<svg viewBox="0 0 300 90" role="img" aria-label="Before dependency structure"><rect x="5" y="10" width="100" height="50" rx="5" fill="#e7edf4"/><text x="20" y="40">Caller</text><path d="M110 35H180" stroke="#52677f"/><rect x="185" y="10" width="110" height="50" rx="5" fill="#e7edf4"/><text x="195" y="40">Module</text></svg>
</section><section><h3>After</h3><p>Replace this description with an SVG of the actual proposed structure.</p></section></div>
<dl><dt>Problem</dt><dd>Concrete friction in the inspected code.</dd><dt>Change</dt><dd>Scoped proposal.</dd><dt>Benefit</dt><dd>Observable maintenance or testability improvement.</dd></dl>
</article><section><h2>Top recommendation</h2><p>Recommendation with evidence.</p></section></main></html>
```

Replace illustrative names and geometry with the inspected code's actual facts.
No dependency is installed by opening the report. Ask which candidate to explore;
do not implement the proposal merely because the report was produced.
