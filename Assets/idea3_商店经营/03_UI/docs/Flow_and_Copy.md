# Flow and English copy

## Screen map

| Screen | Purpose | Entry / return | Current game mapping |
|---|---|---|---|
| 01 Main Menu | Continue, New Diner, How to Play, Settings; save submenu | Initial view / pause → menu | `onNew`, `onContinue`, `onMenu`, `onImport`, `onSave` |
| 02 Planning | All 7 purchase quantities and reserve | New run or next day → Open | `openDay(purchaseMap)` |
| 03 Recipe Book | Exact counts for all 3 burgers | F / button → Esc or Back | `RECIPES`, `INGREDIENTS` |
| 04 Live Service | Sparse HUD and table tickets | Successful open | `phase=open`; `state.objective` |
| 05 Take Order | Contextual table action | Focus occupied table → E | `take-order` |
| 06 Grill Cooking | One active meal, time boundaries | Raw meal → grill → cooked meal | `place-grill`, `take-food` |
| 07 Toppings | Exact checklist, including 1/2 onions | Cooked meal → board | `put-food`, `add`, `reset-toppings`, `plate-food` |
| 08 Carry & Serve | Held tray matched to recipe/table | Plated meal → matching table | `serve` |
| 09 Order Book | Exactly tables 02, 03, 04 | Tab / order queue | `guests`, `orders` |
| 10 Closing | No arrivals; finish current guests | Manual close or 480s elapsed | `requestClose()` / automatic transition |
| 11 Shift Summary | Cash and profit shown separately | Every guest gone | `_finishIfReady()` |
| 12 Upgrades | Exactly 3 existing upgrades | Planning or summary | `buyUpgrade(id)` |
| 13 Pause | Resume, help, save files, settings, close, menu | Esc | Current blocking pause mechanism |
| 14 Settings | 4 audio sliders, look sensitivity, control reference | Menu or pause | Existing preference fields |
| 15 How to Play | Entire operating loop | New help entry | Proposed informational UI |
| 16 Low Funds | Reserve rejection and existing recovery paths | Failed purchase validation | Existing constraints; proposed explanatory panel |
| 17 State & Confirmations | Six modal templates, feedback | Design board | Proposed confirmation UX |
| 18 Components | Typography, palette, tickets, icons | Design board | Design reference |

## The complete loop

Main Menu → Planning → Open → Guest enters, sits, requests order → Take Order at table → Choose recipe at bun station → Carry raw meal to grill → Cook → Take cooked meal → Put on board → Add exact toppings → Plate & Pick Up → Carry matching recipe to table → Serve and receive payment → Repeat → Closing (no arrivals) → All guests leave → Summary → Optional upgrade → Plan Next Day.

Tables are `table02`, `table03`, `table04`. Five actor templates rotate (`vera`, `gus`, `lou`, `pip`, `nora`); only three table slots may be active. One meal can be in preparation or held at a time. Default shift length is 480s; customer limit is 12. Guests have 150s patience after sitting and 195s with Comfortable Seats. Guest motion / eating continues while the shift is running.

## Menu and purchase reference

| Recipe | Exact ingredients | Cost | Sale |
|---|---|---:|---:|
| Classic Burger | Bun ×1; Patty ×1; Onion ×1; Cheese ×1 | $10.50 | $18 |
| Onion Burger | Bun ×1; Patty ×1; Onion ×2; Pickle ×1 | $11.50 | $22 |
| Double Burger | Bun ×1; Patty ×2; Lettuce ×1; Tomato ×1 | $16 | $28 |

Ingredient costs: Buns $3, Patties $6, Onions $1, Lettuce / Tomato / Cheese / Pickles $0.50 each. Recommended purchase: 12 / 14 / 16 / 6 / 6 / 8 / 6 in that ingredient order, total $149. At starting cash $200, cash after purchase is $51, reserve is $35, unreserved cash is $16. The reserve is not charged at purchase; $35 is charged at closing.

## Sample values are independent snapshots

The 16 screens demonstrate different states rather than one continuous captured playthrough. Live HUD cash $119 is valid after the recommended $149 purchase and one Classic, one Onion, one Double sale ($68). The Onion meal shown in assembly is the next active meal. Cooking screenshot time 8.2s lies within the standard ready window [6s,14s).

The summary example is an internally consistent completed shift: opening cash $200 − stock paid $149 + sales $216 − overhead $35 = closing cash $232. Sales: 4 Classic + 4 Onion + 2 Double = $216. Ingredients used: 4×$10.50 + 4×$11.50 + 2×$16 = $120. Net profit: $216 − $120 − waste $0 − overhead $35 = $61. Inventory remaining: buns 2, patties 2, onions 4, lettuce 4, tomato 4, cheese 4, pickles 2; value $29. Each fresh topping quantity is below 5, so `floor(quantity×0.2)` is zero; this sample needs no Cold Storage. 10 served / 2 lost fits the 12 guest limit. No refunds are fabricated or offered.

## Settings and controls

Master volume 65%, Music 40%, Sound effects 80%, Ambience 30%; range 0–100%. Look sensitivity 100%; range 20–200%. These are existing defaults and ranges. Control labels are reference, not a new remapping feature. WASD Move; Mouse / Drag Look; E Interact; F Open Recipes; Tab Show/Hide Orders; Esc Pause/Back. Settings save locally on input, so no false Apply button is shown.

## Copy source

`English_Copy.csv` lists every visible text node with its screen, font and pixel size. All UI wording in screen and board assets is English. Source background signs are part of the existing restaurant scenes. The gallery is a design browser; mockup buttons are illustrative and do not operate the game.
