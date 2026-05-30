# NetraMesh Labs — Corporate Website

A fully static, secure, bilingual (EN/ID) marketing & branding site for **NetraMesh Labs**
(`netramesh.com`) — a cyber technology company offering SOC Dashboard, SIEM, SOAR, UEBA,
CMDB, Case Management, Incident Response, Sandboxing, and Vulnerability Management.

## Highlights

- **100% static** — HTML + CSS + vanilla JS. No backend, no login, no database, no cookies.
- **Zero third-party dependencies** — no CDN, no Google Fonts, no analytics, no trackers.
  Everything is self-hosted, which keeps the Content-Security-Policy strict (`'self'` only).
- **Dark-first cybertech theme** built on the brand palette.
- **Bilingual** EN/ID toggle (the only thing stored is a UI language preference in `localStorage`).
- **Animated mesh network** hero (HTML canvas), scroll-reveal, animated stat counters, orbit visual.
- **Responsive** down to small mobile, with an accessible slide-in menu.
- **Accessible** — skip link, focus states, semantic landmarks, `prefers-reduced-motion` honored.

## Structure

```
netramesh-website/
├── index.html              # single-page site (Home, Products, Solutions, Platform, About, Contact)
├── assets/
│   ├── css/styles.css
│   ├── js/main.js
│   └── img/favicon.svg
├── _headers                # security headers for Netlify / Cloudflare Pages
├── .htaccess               # security headers + HTTPS redirect for Apache
├── robots.txt
└── sitemap.xml
```

## Run locally

It is pure static, so any static server works. For example:

```bash
cd netramesh-website
python3 -m http.server 8080
# then open http://localhost:8080
```

> Opening `index.html` directly via `file://` mostly works, but the strict CSP and the
> canvas animation behave best when served over HTTP.

## Deploy

| Host | What to do |
|------|------------|
| **Netlify / Cloudflare Pages** | Drag-drop the folder. `_headers` is applied automatically. |
| **GitHub Pages** | Push the folder; set custom domain `netramesh.com`. (Note: GH Pages ignores `_headers`/`.htaccess` — add headers via Cloudflare proxy in front.) |
| **Apache** | Upload to webroot; `.htaccess` applies headers + forces HTTPS. |
| **Nginx** | Serve the folder and add the headers below to your `server {}` block. |

### Nginx header snippet

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self' mailto:; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests" always;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), interest-cohort=()" always;
server_tokens off;
```

## Security notes

- **CSP** blocks all inline scripts/styles and any external origin — there are none in the code,
  so the policy is genuinely `'self'`-only (no `unsafe-inline`).
- **No data leaves the browser.** The "Request Demo" form does not POST anywhere; on submit it
  builds a `mailto:hello@netramesh.com` link with the fields URL-encoded and opens the user's
  mail client. Nothing is stored or transmitted by the site.
- **HSTS + HTTPS redirect**, `X-Frame-Options: DENY` (clickjacking), `nosniff`, locked-down
  `Permissions-Policy`, and server-token suppression are included.
- Recommended after deploy: test on https://securityheaders.com and https://observatory.mozilla.org.

## Customization

- **Colors:** edit the `:root` tokens at the top of `assets/css/styles.css`.
- **Copy / translations:** every translatable element has `data-en` and `data-id` attributes in
  `index.html`. Edit both to change wording. The visible default text should match `data-en`.
- **Contact email:** search for `hello@netramesh.com` in `index.html` and `main.js`.
- **Products/Solutions:** duplicate a `.card` / `.solution` block in `index.html`.
- **Brand assets:** `tools/build-assets.py` (pure-Python, no dependencies) derives three assets from the
  uploaded master logo `assets/img/NetraMeshLabs.png`:
  - `logo-icon.png` — the eye+mesh icon, auto-cropped & transparent, used in the navbar/footer
    (the wordmark text beside it stays as HTML so it reads on the dark theme).
  - `favicon.png` — 64×64 icon for the browser tab.
  - `og-image.png` — 1200×630 share card (referenced by `og:image` / `twitter:image`) for link
    previews on WhatsApp, LinkedIn, X, Slack, etc.
  Re-run `python3 tools/build-assets.py` after replacing the master logo or editing the script to regenerate
  all three. After deploying, validate previews with the LinkedIn Post Inspector and Facebook
  Sharing Debugger (they cache aggressively — re-scrape when you update the image).
