# Technical handoff · UI Management V2

## Delivery scope

16 screen designs plus 2 design boards at 1920×1080, each in native SVG, rendered PNG and portable inline-SVG HTML. This package is visual design and implementation guidance. Runtime management-flow.js / management-ui.js, assets, and previous UI v1 remain untouched. Scene screenshots are copied from existing game art and embedded in screen SVGs for portability. UI text, shapes, rules and icons are native vector elements, not bitmap lettering.

## Preserve the implemented game

Read `web_demo_v1/dist/js/management-flow.js`, `management-ui.js` and `management-app.js` before implementation. Keep these existing mechanics: planning/open/closing/summary phases; 7 ingredient ids; 3 recipes and prices; 3 table slots (02–04); 5 rotating actors; a single prep/held meal; exact ingredient checks; standard grill ready 6s, burnt 14s; upgraded grill ready 3s, burnt 8s; closing waits for all guests to become gone; 20% floor topping spoilage without storage; $35 closing overhead; current save validation and local audio preferences.

Existing upgrades: Cold Storage $100 retains unused fresh toppings; Fast Grill $120 changes timing to 3s/8s; Comfortable Seats $150 adds 45s to patience. Upgrades can only be bought during planning and summary. Do not substitute new upgrades, grants, refunds, extra table slots, partial recipe checks, multiple cooking slots, delivery mechanics or a web Exit action.

## Proposed UI improvements (not existing features)

| Proposal | Required implementation | Rule impact |
|---|---|---|
| Persistent Next Step HUD | Bind to `state.objective`; refresh on state change | None |
| Compact contextual action panels | Present `getActions(target)` near edge / bottom instead of every action in full overlay | None; keep enabled reasons |
| How to Play | Informational overlay available from menu/pause | None |
| Save submenu | Move existing import/export under Save files; preserve result/status feedback | None |
| Confirmation modals | Confirm New Diner, import replacement, manual closing, discard and topping reset before existing callback | None after confirmation |
| Upgrade warning | Compute cash after upgrade and remind user of supplies + $35 reserve | Warn only; don't add a new affordability restriction |
| Low-funds recovery panel | Explain reserve math; return to editable quantities or existing main-menu import/new paths | No bailout, refund or free stock |
| Order Book states | Expose current table guest states; full book via UI action when needed | No new guest states |

The smallest complete fresh Classic costs $10.50 and the operating reserve is $35; a new empty-stock run needs $45.50 for a fully serveable meal. Current `openDay` checks buns and patties only ($9 plus reserve); do not silently strengthen this rule in a visual restyle. Low-funds guidance says complete recipe rather than claiming the minimum-open check guarantees a meal. A low-funds run without a serveable recipe can recover by importing a valid saved run or explicitly beginning a New Diner. Those are existing actions, proposed to be surfaced more clearly.

## Layering and blocking

0 game view; 10 minimal HUD; 20 nonblocking order tickets; 30 focus/held indicators; 50 planning/summary/pause/settings/help/recipe modal; 60 confirmation; 70 toast/status. A blocking overlay must suppress world movement, interaction and timers through the app's `onBlocking` / `syncPause` path. A compact context panel that only previews the current interaction should not accidentally pause cooking or patience. Avoid obscuring the center crosshair area or duplicating the same action at several places. Esc returns to the actual originating overlay, not always the diner. Trap keyboard focus inside blocking panels and restore it to the initiating control. F opens Recipes; Esc/Back closes it. Tab has its current live HUD toggle meaning. Keybindings shown here are a reference, not editable settings.

Context action state must come from `getActions` and exact recipe checks; don't infer readiness from elapsed time alone or from a partial count. Toppings are incremented one unit at a time. 1/2 onions is unfinished; extra ingredients also block plating. Topping reset records removed toppings as waste; discarding a meal records its used ingredients as waste. Burnt meals must go to the dish return. Serving is only valid when guest recipe, cooked quality and all ingredient counts match. Guest payments are received when served.

## Style, layout and export details

Forest #183E34; cream #F7F1E4; paper #FFF9ED; mint #BDD6C4; sage #7FA58E; coral #CC775F. Coral is restrained for warnings and irreversible actions. Labels and digits remain dark enough to read on cream. Use shape + text (READY / BURNT / counts) as well as color. Georgia Bold for large display / burger names, Arial for body and controls. Live critical text should be 22–24px at 1080p; small metadata is 14–18px. Default buttons are 60px high; pointer targets at least 44px. Native icon masters use a 64×64 viewBox and 3px round stroke. 8px spacing rhythm; paper corner radius 16–24px; no redrawing of existing scene props is necessary.

The 1920×1080 canvases are authoritative widescreen mockups. Scale HUD anchors relative to edges and make management forms responsive at integration; this package does not claim tested runtime layouts on phones or other aspect ratios. Background crops use `xMidYMid slice`. Every screen embeds the actual scene image, which can be replaced by the runtime game view. Game runtime text should remain DOM/TMP text so localization and accessibility survive implementation. No font files are distributed.

`assets/panels/` contains **12** background-only transparent SVG/PNG pairs. Text and icons are deliberately absent from these stretchable pieces and must be composited separately. `manifest.json` stores the actual source size and four equal insets: corner radius + 3px (e.g. panel_paper 27px; button_primary 15px; keycap 9px). These preserve the vector-rounded corners and border under nine-slice scaling. They are real source-space guides, not already-built engine materials. Corners stay fixed; edges and center stretch; never shrink below 2×inset+1px. Chip assets are pill-like at source size and require these minimum dimensions. `progress_track` needs a separately sized fill. Native PNG alpha is preserved. **23** icon pairs are single-scale icons and must not be nine-sliced.

SVG names are stable (`01_MainMenu.svg` through `18_Components.svg`); text is editable `<text>`, shapes remain vectors, background is embedded PNG. HTML per screen is a preview wrapper around the same native SVG. `gallery.css` styles the local gallery only; it is not a replacement game stylesheet. The generator is `idea3/tools/build_ui_management_v2.py`, reproducible and wholly separate from the runtime. Browser rendering uses Edge with a task-specific D-drive profile, cache and TEMP/TMP.

## Validation

The renderer records screen text bounds and a local-file gallery interaction check in `qa/layout_and_gallery.json`. Inspect the contact sheet and selected full PNGs as visual QA; automated viewport bounds do not by themselves detect every internal text collision. All asset PNGs must have the exact manifest dimensions and alpha channel. No live gameplay, engine integration, runtime screen reader behavior or responsive gameplay layout is validated by this design package.
