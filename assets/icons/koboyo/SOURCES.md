# Koboyo icons · provenance and terms

Hand-drawn SVG icons, fetched from https://koboyo.com/icons/svg/<name>.svg on
2026-08-19, for use as **part-opener subject marks** (design-rules.md §3: one
oversized subject mark, no text of its own, reversed out of the lime field).

**Terms** (https://koboyo.com/icons/license, read 2026-08-19): free for personal
and commercial use; attribution never required; embedding in a product is
permitted "as long as the icons are part of something bigger rather than the
product itself". Redistributing the library as a competing icon product, or
building a competing icon/canvas product from it, is not permitted — which is
why only the icons actually used are vendored here rather than the set.

**Why this library and not Lucide**, which this package already ships: these are
**fill-based** (`fill="currentColor"`, no stroke), and a subject mark is rendered
at display scale. A stroked icon scaled to that size renders as the accident
design-rules.md §6 records; a filled silhouette renders as a deliberate graphic.
Lucide remains the semantic inline set at 14-24px.

| file | mark | used on |
|---|---|---|
| key.svg | key | Part A opener |
| globe.svg | globe | Part B opener |
| rocket.svg | rocket | Part C opener |

## Scenario step and persona marks (added 0.1.522.r4)

The files in the table below, from the same source and under the same terms,
fetched 2026-08-19 — the table is the count, a number in this sentence was
wrong once — used as the **step and persona icons** on the four scenario pages.
They are inlined as nested `<svg>` scaled into a fixed box, so `preserveAspect`
does the fitting: the files carry their own proportions and forcing a square
squashes the wide ones (`dumbbell` is 198x97).

**One was the wrong object and only the contact sheet caught it.** `file.svg` is
a nail file, not a page: it renders as a thin diagonal. It shipped into two
figures, resolved fine, scaled fine and passed every gate. `document.svg` is the
page. An icon that is the wrong *thing* is invisible to every check this package
has.

| file | mark |
|---|---|
| archive.svg | archive |
| bell.svg | bell |
| bookmark.svg | bookmark |
| calendar.svg | calendar |
| chart.svg | chart |
| check.svg | check |
| clipboard.svg | clipboard |
| clock.svg | clock |
| coffee.svg | coffee |
| credit-card.svg | credit card |
| cup.svg | cup |
| document.svg | document |
| dumbbell.svg | dumbbell |
| file.svg | file |
| gift.svg | gift |
| hand.svg | hand |
| list.svg | list |
| mail.svg | mail |
| message.svg | message |
| receipt.svg | receipt |
| scale.svg | scale |
| shield.svg | shield |
| undo.svg | undo |
| user.svg | user |
| wallet.svg | wallet |
| bot.svg | bot |
| briefcase.svg | briefcase |
| car.svg | car |
| code.svg | code |
| cpu.svg | cpu |
| shopping-bag.svg | shopping bag |
| store.svg | store |
| truck.svg | truck |
