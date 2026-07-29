# BREW

## Project Overview

A gamified morning-routine habit tracker with a café/coffee theme. Completing all 4 blocks "makes a brew":

- **B** Begin with barakah — tahajjud, Quran, Fajr, dhikr
- **R** Read & reflect — reading, journalling, writing, reflection
- **E** Exercise & energise — running, pilates, walking, sport
- **W** Work — creative, occupational, sidequest, volunteer, study

**Streak rule:** 3 full brews (all 4 blocks completed) in a calendar week.

**Target users:** Muslim women building intentional morning routines.
**Vision:** Web prototype first (`index.html`), then native iOS app (SwiftUI, EventKit, camera, haptics).

---

## Technical Overview

### Critical constraint
**All app logic and styling lives in the single file `index.html`.** No external `.js` or `.css` for app code. Everything inlined. Reason: `file://` URLs and in-app preview panels don't load external resources. Do not split until the native iOS port.

**The only exception is PWA deployment infra** (see below): `manifest.json`, `sw.js`, `icons/`. These carry no app logic, and `index.html` still runs standalone from `file://` without them — the service-worker registration is guarded on `http(s):` and fails silently.

### File structure (inside index.html)
1. `<script>` block 1 — **BrewStore IIFE** — entire data layer, settings, migrations
2. `<script>` block 2 — **Daily Grind** — pixel cup, block ticking, celebration, day navigation
3. `<script>` block 3 — **Planner / Calendar / Progress / Settings / Nav**
4. `<script>` block 4 — **PWA** — service-worker registration + add-to-home-screen hint
5. Inline `<style>` — all CSS
6. Inline HTML — all views and modals

### PWA (installable, offline) — added 2026-07-30
Lets testers install BREW to their home screen with no App Store, no Apple Developer account.

| File | Purpose |
|------|---------|
| `manifest.json` | name/icons/colors, `display: standalone`, `start_url: "./"` — relative so it survives any deploy path |
| `sw.js` | offline shell. Precaches 8 files. **Navigations are network-first** (a reload always gets the newest build) with cache fallback; other same-origin GETs are cache-first. Bump `CACHE` on deploy. |
| `icons/*.png` | 32/180/192/512 + a 512 maskable (extra padding for Android's mask). `icon-180` is the `apple-touch-icon`. |
| `tools-mkicons.py` | regenerates every icon from the app's own 18×20 `POT` pixel art, reusing the same band + dither logic, so icons always match the cup. Needs only stdlib (`zlib`). |

iOS notes that matter:
- iOS has **no install prompt** — Share → Add to Home Screen is the only route, so the app shows a dismissible hint bar (`.a2hs`) explaining it. Android/Chrome instead get a real **Install** button via `beforeinstallprompt`.
- The hint never shows when already installed (`display-mode: standalone` / `navigator.standalone`), and waits for the onboarding/welcome modals to close first.
- `viewport-fit=cover` + `env(safe-area-inset-*)` on `.app` and `.tabbar` keep content clear of the notch and home indicator.
- **Installed iOS PWAs get their own storage container**, separate from Safari's. Data ticked in Safari does not carry into the installed app — tell testers to install first, then use only the installed icon.
- Installed PWAs are exempt from Safari's 7-day storage eviction; browser tabs are not. Another reason to install.

### Testing
Logic verified via `osascript -l JavaScript` (JavaScriptCore). Stubs required:
```js
const console={log:()=>{},error:()=>{}};
const localStorage={_d:{},getItem(k){return this._d[k]??null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}};
const setTimeout=()=>{};
const requestAnimationFrame=()=>{};
```
After edits: `open "index.html"` and Cmd+R in browser.

**Testing the PWA bits** needs a real `http://` origin (service workers and `manifest.json` never work on `file://`). The sandbox blocks a server from reading files under `~/Desktop`, so mirror the files to `/tmp/brewprev` and serve that — this is what `.claude/launch.json` points at:
```bash
mkdir -p /tmp/brewprev/icons && cd "/Users/amnaikhwan/Desktop/BREW app" && cp index.html manifest.json sw.js /tmp/brewprev/ && cp icons/*.png /tmp/brewprev/icons/
```
Re-copy after every edit — the mirror is a snapshot, not a symlink.
Then verify in the browser pane: registration + `caches.keys()`, then stop the server and reload — the app must still render. To prove the network is genuinely down, fetch a URL that is *not* precached (a cached one is served by the SW and looks like success either way).

Gotchas hit while verifying, worth not repeating:
- Don't hand-mutate modal classes to "preview" UI state; it leaves the app in a state it never reaches naturally and produced a false regression report.
- `computer` click coordinates are **screenshot-pixel** space, which is not CSS space when the screenshot is scaled. A ref-click that silently misses looks exactly like a broken event handler. Confirm with `elementFromPoint` or a synthetic `.click()` before concluding anything is broken.

### localStorage keys
| Key | Content |
|-----|---------|
| `brew.plans.v2` | `{ [mondayDateStr]: { blocks: { B,R,E,W: { slot:{start,duration}, items:[{id,label,emoji}] } } } }` |
| `brew.comp.v1` | `{ [YYYY-MM-DD]: { [blockLetter]: [itemId, ...] } }` |
| `brew.disp.v1` | display/UI prefs |
| `brew.log.v1` | `{ [timestamp]: { ts, b, id, label } }` — append-only tick log |
| `brew.meta.v1` | `{ schema: 3 }` — current schema version |
| `brew.settings.v1` | location, block defaults (offsets/gaps/durations), activity menus |
| `brew.edited.v1` | `{ [YYYY-MM-DD]: true }` — days that were back-filled/edited retroactively |
| `brew.notes.v1` | `{ [YYYY-MM-DD]: "text" }` — optional morning notes per day |
| `brew.celeb.v1` | `{ [YYYY-MM-DD]: true }` — celebration tracking |
| `brew.welcomed` | `"1"` once info modal shown — controls first-launch auto-show |
| `brew.onboarded` | `"1"` once the name prompt is answered or skipped |
| `brew.a2hs` | `"off"` once the add-to-home-screen hint is dismissed or the app is installed |

### IndexedDB
Store `brew-photos`, object store `photos` keyed by `{date, block, id}`. Blob photo data. UI not yet built.

### Key terminology
- **Plan** = per-week schedule. Key = Monday date string `YYYY-MM-DD`.
- **Items** = activities inside a block (NOT "activities" — that was v1 schema).
- **Completion** = which item IDs ticked on a given date.
- **Block slot** = `{start: minutesFromMidnight, duration: minutes}`.

### Schema migrations
- v1→v2: `activities` → `items`, single plan → per-week map.
- v2→v3: removes stale `starterItems` from settings, repairs pruned activity menus by re-adding missing CATALOG items.

---

## Design Principles

### UI/UX philosophy
- Warm café aesthetic: cream/brown palette, system-ui/serif font mix
- Receipt/slip metaphor for block cards (torn-edge bottoms, pin decorations)
- Pixel-art latte cup as the central Daily Grind visual
- Hijri date shown alongside Gregorian throughout
- 7-cycle deterministic mug sticker rotations on completed brew days

### Coding conventions
- No external dependencies — everything inline in `index.html`
- BrewStore IIFE exposes `window.BrewStore` (aliased `S`) as the sole data API
- Settings use a draft/override pattern: `setSettingsOverride()` for preview, `clearSettingsOverride()` to discard, `applyChanges()` to persist
- Block chaining: only B is sunrise-relative (offset); R/E/W chain from previous block's end (gap)
- `blockStart(b, sr)` recursively resolves chain; supports both sunrise-relative and fixed modes
- Per-week undo/redo stacks in planner (JSON snapshots, max 60)

### Constraints to preserve
- Default blocks always have empty items (never pre-populate from saved routine)
- Celebration fires on tick transition (`!fullBefore && fullNow`), not on page load
- Past days are view-locked by default; explicit unlock marks them as back-filled
- `confirm()` dialogs used for destructive actions (will become native UIAlertController in iOS port)

---

## Current State

### Implemented features

**Daily Grind (default view):**
- 18×20 pixel-art latte cup on `<canvas>` with dithered band blending
- Day navigation arrows (browse past days, "Back to today" pill)
- Past-day locking with "🔒 Edit this day" unlock; "✎ edited later" tag on back-filled days
- Edit-block icon (✎) on slip headers → opens that block's planner menu (with commit-unlock confirm)
- Celebration overlay on cup-fill transition; replays on empty→fill but not on reload
- Morning notes textarea below order slips
- Items as tickboxes; can't tick if block has no items planned

**Order Ahead (planner):**
- 2×2 receipt slips with dropdown menus; click anywhere on slip to open menu
- Draggable/resizable blocks on 3am–1pm timeline with sunrise marker
- Undo/redo (↩↪) + "Repeat last week"
- Commit/save, ICS export, Google Calendar export (per-block)
- Collapsible "Save as default schedule" (sunrise-relative or fixed modes)

**Settings:**
- Location picker (10 cities with IANA timezones) for accurate sunrise
- Block time defaults (offset/gap/duration controls, 5-min increments)
- Activity menu customization (add custom, drag-to-reorder, reset)
- Deferred-edit model: changes preview live, "Apply changes" bar to persist

**Progress:**
- 4 SVG closing rings (Apple Fitness style), 2×2 grid
- Daily log receipt with timestamps

**Calendar (Month + Week views):**
- Month: grid with Hijri dates, mug stickers on brew days, concentric week rings in right rail
- Week: B/R/E/W tile squares, mug stickers, pencil indicators on edited days, morning notes

**Sunrise:**
- NOAA algorithm with timezone-aware calculation (`Intl.DateTimeFormat` for DST)
- Fallback to pre-loaded UK mid-latitude monthly averages
- Cities carry IANA `tz` field for correct local sunrise

### BrewStore API (abbreviated)
```js
S.weekKey(date?)           // → "YYYY-MM-DD" (Monday of week)
S.getPlan(wkKey)           // → plan object (creates default if missing)
S.savePlan(wkKey, plan)
S.getComp(date)            // → { B:[ids], R:[ids], ... }
S.toggleItem(date,b,id)    // tick/untick; updates log
S.getLog(date)             // → [{ts,b,id,label}] sorted asc
S.weekFullBrewDays(wkKey)  // → count of days all 4 blocks completed
S.streak()                 // → current weekly streak count
S.getSettings()            // → settings (returns draft override if active)
S.getSavedSettings()       // → persisted settings (ignores override)
S.getNote(date) / setNote(date, text)
S.isBackfilled(date) / markBackfilled(date)
S.saveRoutineFromWeek(wk, mode)  // "sunrise" or "fixed"
```

---

## Known Issues

- Sunrise table fallback is UK mid-latitude averages; only accurate when a city is selected in Settings
- Preview panel is render-only (no tap interactions) — expected limitation
- `confirm()` dialogs appear as browser-native; will need native replacement in iOS port

---

## Next Priorities

### Gamification (next web session)
- **Badges** — earn badges for completing activities, streaks, milestones
- **Coffee beans** — earn currency by completing blocks/brews
- **Mug shop** — spend beans to unlock different pixel-art mugs to display on Daily Grind

### Trials (current)
- **The PWA is the trial vehicle** — testers install from the Netlify URL, no App Store or Apple Developer account needed.
- Native iOS is deliberately deferred: TestFlight requires the **$99/yr Apple Developer Program**, and a free Apple ID can only sideload to your own device with builds that expire after 7 days. Not viable for outside testers.

### iOS App (later major milestone)
- The web prototype (`index.html`) is feature-complete enough to start the iOS port
- Stack: SwiftUI, EventKit (calendar export), camera (photo stamps), haptics
- The web app serves as the full design/logic spec for the native build
- Do NOT split index.html into separate files until the iOS port begins
- Prerequisites not yet in place: full **Xcode** is not installed (only Command Line Tools), and no Apple Developer account

### Not yet built (web)
- Photo capture / stamps (IndexedDB store ready, UI not built)
- Strava-style social feed

### Improvements to consider
- Calibrate sunrise to user's actual geolocation (beyond city picker)
- Offline-first sync strategy for eventual multi-device support

---

## Session Notes

> Keep concise. One line per item. Most recent at top.

- **2026-07-30:** Made the app an installable PWA (manifest, service worker, icons generated from the app's own mug art, iOS add-to-home-screen hint, safe-area insets). Verified offline load with the server stopped. Chose PWA over a native port for trials — TestFlight needs a paid Apple account and Xcode isn't installed.
- **2026-06-27:** Git repo initialized; pushed to github.com/kataura-source/brew-app (account was later renamed from `amnaaikhwan-source`); connected to Netlify with auto-deploy on push to main. **Live URL: brewappweb.netlify.app** (renamed 2026-07-30 from `brewappwebtest3`). Nothing in the code hardcodes the domain — manifest `start_url`/`scope` and all asset paths are relative, so renaming the site again needs no code change.
- **2026-06-27:** Reorganized CLAUDE.md to serve as single source of truth with structured sections.
- **2026-06-27:** Verified g-edit absolute positioning fix — all 4 slips render within viewport, no overflow.
- **2026-06-27 (earlier session):** Added edit-block icon (✎) on Grind slips → opens planner menu with commit-unlock confirm. 7-cycle deterministic mug sticker rotations. Mug/pencil positioning refined (mug in bsq-group, pencil in dnum-row). Undo/redo changed to horizontal ↩↪. Whole-receipt clickable in planner. Celebration replays on empty→fill transition only.
- **2026-06-27 (earlier session):** Morning notes feature. Back-filled day tracking with pencil indicators. Past-day locking with unlock flow. Day navigation arrows on Daily Grind. Settings deferred-edit model with Apply changes bar. Drag-to-reorder fix (document-level listeners). Migration v3 (repair pruned menus, remove starterItems). Timezone-correct sunrise with IANA zones. Block chaining (R/E/W relative to previous block, not sunrise). Save routine from planner (sunrise-relative or fixed).
