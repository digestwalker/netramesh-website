# Deploying NetraMesh Labs to cPanel (Apache)

The site is 100% static, so deployment is just uploading files into your domain's
document root. The included `.htaccess` handles HTTPS redirect, security headers, and caching.

**Deploy package:** `netramesh-cpanel.zip` (everything you need, nothing you don't —
the 1.3 MB master logo, the Netlify `_headers` file, and README/docs are intentionally excluded).

---

## 1. Point the domain at the server (if not already)
- In your domain registrar, set the **nameservers** to your host's, or add an **A record**
  for `netramesh.com` (and `www`) pointing to the cPanel server IP.
- In cPanel, `netramesh.com` should be your **primary domain** (doc root `public_html`).
  If it's an **addon domain**, note its doc root (e.g. `public_html/netramesh.com`) and use
  that wherever this guide says `public_html`.

## 2. Turn on SSL FIRST  ⚠️
The `.htaccess` forces HTTP → HTTPS. If you upload before a valid certificate exists, the
site will fail to load (cert error / redirect loop). So **do this before step 3**:
- cPanel → **SSL/TLS Status** → select `netramesh.com` + `www` → **Run AutoSSL**.
- Wait until both show a valid (green) Let's Encrypt certificate.

## 3. Upload & extract
1. cPanel → **File Manager** → open `public_html`.
2. (Settings, top-right) → tick **Show Hidden Files (dotfiles)** so `.htaccess` is visible.
3. **Upload** → choose `netramesh-cpanel.zip`.
4. Back in `public_html`, right-click the zip → **Extract** → extract into `public_html`.
5. Confirm these now sit directly in `public_html` (NOT inside a subfolder):
   `index.html`, `.htaccess`, `robots.txt`, `sitemap.xml`, and the `assets/` folder.
6. Delete `netramesh-cpanel.zip` afterwards.

> If you already have placeholder files (e.g. a `default.html` or cPanel's `index.html`),
> remove them so `index.html` is served.

## 4. Permissions (usually already correct)
- Folders `755`, files `644`. File Manager → select all → **Permissions** if needed.

## 5. Verify
- Visit **https://netramesh.com** — the site loads, dark theme, animations, dashboard mockups.
- Visit **http://netramesh.com** — it should 301-redirect to `https://`.
- Toggle **EN/ID**, press **`/`** for the command palette, click a product card → it jumps to
  the matching console tab. Resize the window to check mobile layout.
- Security headers: scan the URL at **https://securityheaders.com** (target A/A+).
- Share preview: paste the URL into the **LinkedIn Post Inspector** and
  **Facebook Sharing Debugger** (they cache — re-scrape after any image change).

## 6. Contact email
The "Request Demo" form and footer use `mailto:hello@netramesh.com`. In cPanel → **Email
Accounts**, create `hello@netramesh.com` so those messages have somewhere to land.

---

## Troubleshooting

**500 Internal Server Error after upload**
A directive in `.htaccess` isn't permitted by your host's `AllowOverride`. Fix in order:
1. Open `.htaccess`, comment out `ServerSignature Off` (put `#` in front), save, retest.
2. Still failing? Comment out the `Header unset Server` line.
3. Still failing? Temporarily comment the whole `<IfModule mod_headers.c>` block to find the
   culprit, then re-enable the lines that work. (mod_headers/mod_rewrite/mod_expires are
   standard on cPanel, so this is rare.)

**Redirect loop ("too many redirects")**
Your SSL is terminated by an upstream proxy/CDN. The `.htaccess` already checks
`X-Forwarded-Proto`, but if it persists, comment out the `# Force HTTPS` block and enable
HTTPS redirection from cPanel → **Domains** → *Force HTTPS Redirect* instead.

**Page loads but unstyled / blank**
Make sure the `assets/` folder uploaded with its structure intact (CSS/JS/images inside
`assets/css`, `assets/js`, `assets/img`). Hard-refresh (Ctrl/Cmd+Shift+R) to clear cache.

**HSTS note**
`.htaccess` sends `Strict-Transport-Security … preload` (2-year). Only keep this if you intend
to serve `netramesh.com` over HTTPS permanently (incl. subdomains). To back off, lower
`max-age` or remove that line before going live.

---

## Deploy via GitHub (recommended — pull/deploy instead of re-uploading)

cPanel's **Git™ Version Control** can clone your GitHub repo and deploy with one click, so future
updates are just: push to GitHub → "Update from Remote" → "Deploy HEAD Commit" in cPanel.
The included `.cpanel.yml` copies only the production files into `public_html` (dev files,
the master logo, `tools/`, and docs stay in the repo and never touch the live site).

### One-time setup
1. **Push the project to GitHub** (see commands below in this file's companion notes / your terminal).
2. **Edit `.cpanel.yml`** — replace `CPANEL_USERNAME` with your cPanel username (and adjust the
   doc root if `netramesh.com` is an addon/subdomain). Commit & push that change.
3. **cPanel → Git™ Version Control → Create**:
   - **Clone a Repository**: ON
   - **Clone URL**:
     - Public repo: `https://github.com/<you>/netramesh-website.git`
     - Private repo: use SSH `git@github.com:<you>/netramesh-website.git` and first add cPanel's
       SSH key (cPanel → **SSH Access** → *Manage SSH Keys*, or the key shown in the Git UI) to
       GitHub → repo **Settings → Deploy keys** (read-only is enough).
   - **Repository Path**: e.g. `repositories/netramesh` (NOT inside `public_html`).
4. After it clones, cPanel detects `.cpanel.yml`. Click **Manage → Deploy HEAD Commit** once to
   publish into `public_html`.
5. Make sure **AutoSSL** is active (see step 2 at the top) and visit `https://netramesh.com`.

### Every update after that
```
# on your machine
git add -A && git commit -m "update" && git push
```
Then in cPanel → Git™ Version Control → **Manage**:
- **Update from Remote** (pulls latest from GitHub), then
- **Deploy HEAD Commit** (runs `.cpanel.yml` → copies files into `public_html`).

> Prefer pure `git pull` with no deploy step? Set the **Repository Path to `public_html`** itself
> when cloning. Then "Update from Remote" updates the live files directly and you can ignore
> `.cpanel.yml`. Downside: the repo's dev files + `.git` also sit in `public_html` — harmless here
> because the `.htaccess` `FilesMatch "^\."` rule blocks access to `.git`/dotfiles, but the
> `.cpanel.yml` approach keeps the web root cleaner.

## Updating the site later (manual alternative)
Edit files locally, re-zip (or upload changed files directly via File Manager), and overwrite.
Because `assets/*` is cached for 1 year, **rename a changed asset** (or append `?v=2` to its
`<link>/<script>/<img>` reference) so browsers fetch the new version. HTML is not cached, so
`index.html` updates are picked up immediately.
