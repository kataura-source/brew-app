# BREW

## Project Overview

A gamified morning-routine habit tracker with a café/coffee theme. Completing all 4 blocks "makes a brew":

- **B** Begin with barakah — tahajjud, Quran, Fajr, dhikr
- **R** Read & reflect — reading, journalling, writing, reflection
- **E** Exercise & energise — running, pilates, walking, sport
- **W** Work — creative, occupational, sidequest, volunteer, study

**Streak rule:** 3 full brews (all 4 blocks completed) in a calendar week.

**Target users:** Muslim women building intentional morning routines.
**Vision:** Web prototype first (`brew.html`), then native iOS app (SwiftUI, EventKit, camera, haptics).

---

## Technical Overview

### Critical constraint
**Single self-contained file: `brew.html`.** No external `.js` or `.css` files. Everything inlined. Reason: `file://` URLs and in-app preview panels don't load external resources. Do not split until the native iOS port.

### File structure (inside brew.html)
1. `<script>` block 1 — **BrewStore IIFE** — entire data layer, settings, migrations
2. `<script>` block 2 — **Daily Grind** — pixel cup, block ticking, celebration, day navigation
3. `<script>` block 3 — **Planner / Calendar / Progress / Settings / Nav**
4. Inline `<style>` — all CSS
5. Inline HTML — all views and modals

### Testing
Logic verified via `osascript -l JavaScript` (JavaScriptCore). Stubs required:
```js
const console={log:()=>{},error:()=>{}};
const localStorage={_d:{},getItem(k){return this._d[k]??null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}};
const setTimeout=()=>{};
const requestAnimationFrame=()=>{};
```
After edits: `open "brew.html"` and Cmd+R in browser. Preview panel is render-only (no taps).

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
- No external dependencies — everything inline in `brew.html`
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

### Not yet built
- Photo capture / stamps (IndexedDB store ready, UI not built)
- Strava-style social feed
- Native iOS port (SwiftUI, EventKit, camera, haptics)

### Improvements to consider
- Calibrate sunrise to user's actual geolocation (beyond city picker)
- Haptic feedback patterns (for native port)
- Offline-first sync strategy for eventual multi-device support

---

## Session Notes

> Keep concise. One line per item. Most recent at top.

- **2026-06-27:** Reorganized CLAUDE.md to serve as single source of truth with structured sections.
- **2026-06-27:** Verified g-edit absolute positioning fix — all 4 slips render within viewport, no overflow.
- **2026-06-27 (earlier session):** Added edit-block icon (✎) on Grind slips → opens planner menu with commit-unlock confirm. 7-cycle deterministic mug sticker rotations. Mug/pencil positioning refined (mug in bsq-group, pencil in dnum-row). Undo/redo changed to horizontal ↩↪. Whole-receipt clickable in planner. Celebration replays on empty→fill transition only.
- **2026-06-27 (earlier session):** Morning notes feature. Back-filled day tracking with pencil indicators. Past-day locking with unlock flow. Day navigation arrows on Daily Grind. Settings deferred-edit model with Apply changes bar. Drag-to-reorder fix (document-level listeners). Migration v3 (repair pruned menus, remove starterItems). Timezone-correct sunrise with IANA zones. Block chaining (R/E/W relative to previous block, not sunrise). Save routine from planner (sunrise-relative or fixed).
