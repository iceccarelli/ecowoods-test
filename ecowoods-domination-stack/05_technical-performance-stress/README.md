# Performance budgets

HTML document budgets, measured by Content-Length or bytes read:

| Path | Budget |
|---|---:|
| / | 180 KB |
| /estimate | 160 KB |
| /pricing | 200 KB |
| other priority HTML | 250 KB |

These are deliberately tight because the 2026-10-29 observation was a homepage around half a megabyte. TTFB on Vercel cache hits is not the problem; bytes are.

No load test against production form endpoints ships in this stack.
