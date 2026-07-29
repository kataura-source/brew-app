# BREW

A gamified morning-routine tracker with a café theme. Complete all four blocks — **B**egin with barakah, **R**ead & reflect, **E**xercise & energise, **W**ork — and you've made a brew. Three full brews in a week keeps your streak.

**Live:** https://brewappwebtest3.netlify.app

---

## For testers — installing BREW

BREW installs to your home screen like a normal app. There's no App Store download and nothing to sign up for. It works offline once installed, and your data stays on your own phone.

### iPhone / iPad
1. Open the link **in Safari** (it has to be Safari — Chrome on iOS can't install it).
2. Tap the **Share** button (the square with the arrow).
3. Scroll down and tap **Add to Home Screen**, then **Add**.
4. Open BREW from the new home-screen icon.

> **Install first, then use it.** iOS keeps the installed app's data separate from Safari's, so anything you tick in the Safari tab won't appear in the installed app.

### Android
1. Open the link in Chrome.
2. Tap **Install** on the banner, or the **⋮** menu → **Install app** / **Add to Home screen**.

### Desktop
Chrome or Edge show an install icon in the address bar. Optional — it works fine as a normal tab.

### Notes
- Your data is stored **only on your device**. It doesn't sync between phone and laptop, and nothing is uploaded.
- Uninstalling clears your data.
- To get the newest version, just open the app while online.

---

## Development

Everything the app does lives in **`index.html`** — all HTML, CSS and JavaScript inlined, no build step and no dependencies. Open it directly in a browser to work on it.

The other files exist only to make it installable:

| File | Purpose |
|------|---------|
| `manifest.json` | app name, icons, colours, standalone display |
| `sw.js` | service worker — offline cache. Bump `CACHE` when deploying. |
| `icons/` | app icons |
| `tools-mkicons.py` | regenerates the icons from the app's own pixel-art mug (`python3 tools-mkicons.py`, stdlib only) |

Service workers need a real `http(s)` origin — they're skipped on `file://`, so opening `index.html` directly still works, just without offline support.

Deploys to Netlify automatically on push to `main`.
