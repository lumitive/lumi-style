# Changelog

Rule revisions come only from review retrospectives (divergence ≥2 → retrospective
→ revision), recorded here with a version bump.

## 0.1.413 — the cover mark is contained, not bled

The cover mark took the full height of its cell and ran past the right margin —
`height: 100%`, `max-width: none`, and a six per cent nudge outward — on the
reasoning that a mark grows better than it clips. Measured on a real cover: 602px
inside a 509px column, reaching the viewport edge while the footer rule stopped
90px short of it. A reader asked for half the page, centred, and was right.

It is now bounded by the cell it sits in and centred there, exactly filling its
column. Height-led is kept, because the route across the mark's top is still the
part that carries meaning; what is gone is the licence to grow past the frame.

**Worth recording: two earlier attempts to fix this failed for a reason that was
not visible from the markup.** `min-width: 0` on the item, then `minmax(0, …)`
on the track, then a `max-width` in the document's own stylesheet — all three
were correct and none applied, because a rule shipped in `tokens/` set
`max-width: none` at equal specificity and later in the file. The document was
never going to win that; the rule that said "bleed" had to stop saying it. Three
rounds of fixing the wrong end, and one query to the browser for which rules
actually matched the element ended it.

## 0.1.412 — a column starved to 34px, the standard order, and a green that clears its floors

**`starved_column` gates.** `.swap` renders on `grid-template-columns: 1fr 34px
1fr` and takes THREE children — a before, an arrow, an after. A deliverable
wrote it with two, so the second half landed in the 34px arrow track and wrapped
one word per line. Every gate passed. Its content was trimmed three times across
three rounds of review before anyone measured the box, which was 34px wide the
whole time.

The finding is a block holding a sentence in a column too narrow for it: four or
more words in under 60px, taller than it is wide. Not "narrow" — a chip and a
number legitimately are.

**A first version of this check tried to count children against grid columns and
was deleted the hour it was written**, because CSS grid flows extra children onto
the next row on purpose: `.gr` carries three children in a two-column grid and
renders correctly, so the check failed the reference fixture on its first run.
The property is real and it is not static. A starved column is measurable only
once rendered, which is why it lives in `inspect_layout.py` and not beside D19.

**The scaffold emits the standard order**, which is the default unless a request
says otherwise:

    cover · agenda · Part A opener · content… · Part B opener · content… · closing

The first version emitted cover, one opener, a run of pages and a closing. That
is not a deck, it is a deck's middle. `--parts A,B` is now two by default,
because one part is not a part.

**The cover and closing set at 58px**, not the part opener's 80. A shipped deck
measures 57.6px on both while its openers measure 80.6, and a reader asked for
the cover to match it: an opener is one line of claim on an empty page, while a
cover carries a title, a support line, an attribute strip and a mark, and 80
crowds them. New token, so the opener is untouched.

Their titles carry **two inks**: the claim in ink, the noun the deck is about in
the live green, so the green marks what the page is for rather than decorating
it.

**`--acc-live` #3E7A2E.** `--acc` is legible and reads brown at figure scale;
`--lime` is a surface and D13 correctly refuses it as a stroke on white at
1.21:1. The new green measures **5.21:1 on white and 3.23:1 on the dark ground**,
clearing the label and stroke floors in both palettes, with `--acc-tint` for the
table row wash. Measured, not chosen by eye.

**`.body.cover-grid` takes `minmax(0, …)` on both columns.** A bare `fr` track
keeps an implicit auto minimum, so a mark cell holding an SVG at its intrinsic
size stretched the track past its share — measured at 602px inside a 509px
column — and ran the composition off the page. `min-width: 0` on the item does
not reach the track, which is why it failed to fix this twice.

**`--preset cover` carries every layer.** Its first cut filled trade blocs and
nothing else — no marks, no cities, no lanes, no signals, no terminator — which
is a preset named for the cover that omitted four of the five things the cover
is made of. A reader spotted it in one look.

## 0.1.411 — Venezuela painted over the whole globe, once a minute

Reported as "the screen flashes about every minute". Measured over 70 seconds of
real frames: one layer, `.gl-land`, jumping 2,071 characters and back inside a
tenth of a second. Reproduced in the emitter at lon0 = 20.3, isolated to a
single country, and then measured properly — **Venezuela's clipped polygon
encloses 3.143e6 square units against a disc of 3.142e6.** It is not a flash. It
is Venezuela, drawn over the entire Earth, for six frames, once per revolution.

**The cause is the closure family's fourth appearance and its first without a
special shape.** The others were a hemisphere, a seam-crosser and a ring whose
longitudes were not unwrapped. This one is an ordinary small country that
happens to graze the limb: its single visible run enters and exits at almost the
same azimuth, and which way the closing arc goes between them is decided by
about 1e-12 of angle. Going the long way sweeps the whole cap.

So the repair is not another rule about direction. It is an assertion about the
OUTCOME: a clipped ring cannot enclose more of the sphere than the ring it came
from, plus the sliver a cap arc adds. Where it does, both closure directions are
tried and the smaller kept. Across all 278 rings at 72 rotations the honest
worst case is 0.0000 steradians of excess; a wrong-way closure is 6.28.

**A caller that vouched for its own handedness is exempt**, and finding that out
cost a round trip: the guard's premise is that `signed_area(ring)` bounds the
honest result, and `signed_area` is meaningless within a hair of a hemisphere —
which the day/night terminator exactly is. Applied there it read a false source
area, fired, and re-inverted the night side that 0.1.399 spent a release
correcting.

**The check took three attempts, and the first two are the lesson.**

The first rendered a revolution at 0.6-degree steps and compared adjacent
frames. That is a good description of what a reader sees and a bad test: the
defect occupies about two tenths of a degree, so the sweep stepped over it and
reported ok with the bug reinstated.

The second asserted the right property — the area invariant — but sampled lon0
every five degrees, and missed it for the same reason. A grid cannot find an
event narrower than its spacing, and nobody knows how narrow the next one is.

The third stopped sampling. The failure is not distributed over the rotation: it
happens when a ring GRAZES the limb, and that longitude is computable from the
ring. Each ring is now placed on its own limb and nudged across it in
twentieths of a degree. Reverting the repair fails it in the message above.

## 0.1.410 — the cover globe, and a preset so a document does not have to know four flags

`globe_svg.py --preset cover` is LUMIVATE's own view: Pacific-centred at
lon0=-160, the trade blocs filled, the terminator off. It exists so a document
does not have to carry four flag values to draw the mark, and so every document
that draws it draws the same one. An explicit flag still wins — a preset is a
starting point, not a lock.

`assets/brand/lumivate/` gains **`globe-cover.svg`** and
**`globe-cover.dark.svg`**, that view at cover scale, self-contained in each
palette. **Two files, not one that adapts**: `prefers-color-scheme` follows the
browser rather than the page a mark is dropped on, so a mark that adapts goes
dark on a light deck read in a dark-mode browser.

`assets/brand/README.md` documents the live recipe — the frame, the runtime, and
`data-globe-print-lon0` for a reproducible export — which is what makes the
rotating globe reachable from any agent with the skill installed: no demo
machinery, no build directory, two commands that already ship.

**D19 earned itself on the first document built after it landed.** The rebuilt
proposal referenced `#i-flow`, an icon this package has never had, and the gate
named it before a reader could. The same rebuild then hit the palette split for
the third time in this repository: `--rg-*` variables live in the SCOPED region
palette and the class-to-fill bindings in the UNSCOPED one, so inlining half of
them gave a globe with every variable defined and nothing bound to it — black,
and looking deliberate. The first two were the brand mark and the region map.

## 0.1.409 — D19: a document that cannot render itself does not ship

A deliverable passed `check_design`, `check_prose` and
`inspect_layout --deliverable`, and reached its reader with **no icons anywhere**,
a blank part opener, and a numbered block whose numbers had come away from their
content. Every rule it broke was already written down. Nothing stopped it.

**D19 gates**, beside D12, D14 and D15, and asserts three things a document can
be wrong about decidably:

- **every reference resolves here.** A `<use href="#x">` needs an `id="x"` in
  the same document. The failing deck carried **zero** of them: the icon sprite
  lives in the reference fixture's BODY, and a document assembled by slicing its
  `<head>` gets the whole stylesheet and none of the icons. Thirteen pages of
  handling terms lost their seal-red shield, and the page ground never drew.
  A `<use>` pointing at nothing is valid markup that renders as empty space;
- **every block carries its contract.** `tokens/` renders `.grades` through
  `.gr` and `.gn`, `.band` through `.k` and `.v`, `.swap` through `.no` and
  `.yes`. A class used without the children its rendering assumes silently
  borrows whatever styling it collides with — `.grades` picked up the `.key`
  callout's red outline and left every paragraph outside the box;
- **a part opener carries `class="page opener"`.** The lime opener is a class,
  not a layout. Without it the page renders blank, which is what a reader
  reported.

This is the deliverable-side mirror of `check_repo.py`'s `probe vocabulary`
guard, which says a class a CHECKER asserts must have a rendering in `tokens/`.
The same sentence turned around: a class a DOCUMENT uses must have the rendering
it is asking for, in the document that uses it.

**Two false starts are worth recording, because both would have made it
useless.** The first collected only `<symbol>` ids and so failed the reference
fixture on its first run — the page ground is a `<g id>`, and `<use>` may
reference any element; a gate whose opening move is to fail the fixture is a
gate nobody keeps. The second matched a block's body with a non-greedy
`(.*?)</\1>`, which stops at the first closing tag of that name and truncated a
`.swap` before its second half, reporting a missing `.yes` that was right there.
A gate that cries wolf teaches its reader to skip the line.

**`scripts/new_deck.py` is the positive half.** It emits a skeleton carrying the
complete preamble — token block *and* sprite *and* ground — a cover, a part
opener with its class, one of every block pattern with the markup that renders
it, and a closing. An author edits content into a structure that already works.
Its own preamble bug is instructive: taking the first `<svg>` after `<body>`
left `#g-ground` dangling, because the fixture opens with two hidden SVGs. A
preamble is whatever comes before the content, and guessing how many elements
that is was wrong twice in one hour.

## 0.1.408 — a dark palette that draws the sphere, not just the dark

0.1.407 got the dark palette into a document. It was reachable and it was not
finished, and the difference is worth naming: the chrome indirects to theme
tokens and those redefine under dark, which is true, and it was not sufficient.

`--gl-plate` resolves to `--ln3`, and on a #1D1D1F page `--ln3` sits so close to
the background that the ocean and the page became one black field. The globe
read as a scatter of continents floating on nothing — every value correct, the
figure gone. The comment in the generator said in as many words that the dark
chrome "needs no separate values"; it needed four.

Water on a dark page is not the absence of light, it is a surface with less of
it. The plate lifts just clear of the background and the graticule, the equator
and the tropics lift with it, because a sphere cue nobody can see is not a cue.

**Every deliverable now ships light and dark, from one build.** The two differ
by exactly the body's class and `data-theme`; every figure in them is
byte-identical, because a dark edition maintained separately is a dark edition
that drifts and the reader who compares the two is the one who finds out. The
`.dark.` in the filename is load-bearing: `inspect_layout.py` infers the palette
from it, so the dark edition is graded dark rather than graded twice as light.

The closing page loses its illustration. A closing that restates the cover's
image is a closing that has nothing of its own to say.

## 0.1.407 — the dark palette reaches a document at last, and the mark stops being a second design

**The dark palette had been unreachable since 0.1.333.** `build_fixtures.py`
inlined only the `:root` block from `tokens/lumi-theme.css`, so `body.dark`
never entered a deliverable — adding the class to a shipped document changed
nothing at all, because the values it redefines were not in the file. Nine
releases of a dark palette that no document could express. It is inlined now,
and the globe reads on black without a single new value: the chrome indirects to
theme tokens and the theme tokens redefine.

**The mark is the cover's globe, not a second drawing of it.** 0.1.405 shipped a
monochrome treatment on the reasoning that a logo has to print in one colour.
That reasoning is sound and the answer was still wrong: a company whose figure
and whose mark disagree has two marks. The monochrome styles are deleted
outright and the mark carries the cover's own look, resolved to literals and
inlined, with its own `prefers-color-scheme` dark variant — so one file is
correct on a white page and a black one and needs nothing from `tokens/`.

Building it turned up a defect the same shape as the mark's whole reason for
existing: the first cut read the SCOPED region palette only, and the chrome
variables — `--gl-plate`, `--gl-graticule`, `--gl-equator` — are emitted in the
UNSCOPED file, because a scoped instance is regions-only by design. Every one
resolved to nothing, `fill` became invalid, and an SVG with an invalid fill is a
black SVG. The whole ocean came out black in both palettes and looked
deliberate.

**A stray checkout poisoned every file-scanning guard.** `check_repo.py` walks
the filesystem rather than git's index, so a Claude Code worktree left at
`.claude/worktrees/` — a full copy of this repository at an older version — was
scanned as if it belonged to the tree. Seventeen failures across three guards,
every one of them true of a checkout nobody was editing. Gitignoring it was not
enough: a guard that reads the disk has to be told what the disk is for, so the
walker now skips dot-directories rather than `.git` alone.

**Figures 1 and 2 are kept as LUMIVATE brand images**, written beside the
document rather than into this package. The line is the one the HS codes and the
lane waypoints already fall on: those figures carry 128 tariff codes, 23 ports
and thirteen shipping routes, which are a deliverable's data. lumi-style ships
the component and its own mark; a figure built from a client's tariff list stays
out, and red line 9 is why.

## 0.1.406 — the land in three weights, and an export that is the same twice

**Continents read as continents.** Every land line was one weight, so a
coastline and a provincial border looked alike and the eye had nothing to group
by — on a figure whose stated job is comparing where one trade bloc sits against
another. The shared-arc topology `build_worldmap.py` already builds is the whole
mechanism and it needs no new data: an arc between two countries is stored once
and referenced by both, so its number of users says what it is.

    548 arcs used by one country  -> coast, 2.6px
    196 used by two, different blocs -> bloc edge, 2px
    570 used by two, same bloc    -> border, 0.8px

The fills lose their strokes; all linework moves to those three layers.
Classified in Python once and carried to the runtime in the markup, which is
the standing lesson of 0.1.404 and 0.1.405: those two releases were spent on
one repair applied to one side of a hand-maintained port.

**Oceania is back, and its absence was a regression I introduced.** 0.1.405 made
countries outside a bloc outline-only, and Papua New Guinea, Fiji, the Solomons,
Vanuatu and New Caledonia belong to no bloc — so an entire continent became
1.2px hairlines around small islands. A coast is a coast whether or not it is in
a bloc, so the same change that weights continents puts them back.

**One horizon.** `.gl-equator` was drawn in the graticule's own ink, so the
figure offered four candidate horizons at nearly equal weight. It gets its own
token now. That is `references/brand.md`'s waterline applied to a sphere: one
horizon where the light collects, and exactly one — the tropics stay dashed and
quiet because they are context for the tilt rather than a line to measure from.

**An export is the same twice.** `export_pdf.py` loaded the page and captured
whatever rotation the browser had reached, so two runs on one unchanged document
produced two different PDFs. The component gains `pin(lon0)`: it sets the view,
stops the clock, and — this is the half that took a second attempt — **resets the
signals to where the emitter put them**. The first version stopped the rotation
and left the signals wherever they had drifted, which gave a correctly pinned
longitude and a different picture every time. A pinned frame has to be
reproducible FROM THE MARKUP or it is not pinned.

Which view a document exports is the document's decision, carried as
`data-globe-print-lon0`. A `beforeprint` listener does the same, so Cmd-P in a
browser gives the frame the PDF gives.

**The deck is three pages and the cover is the globe.** The live figure moved
from an interior page to the cover, where `cover-grid` gives it a larger cell
than it had, and Figure 1's page is gone. It opens on the Pacific — the one view
where every lane is visible at once — and exports on Singapore. The legend went
with the page it stood on; what it did, the marks do through their own titles
and hover.

## 0.1.405 — LUMIVATE's mark, a lock with teeth, and the ring's last hiding place

**The brand directory.** `assets/brand/lumivate/` carries two globe marks,
generated by `scripts/build_brand.py` from the same projection and topology as
the figures — so the mark on a cover and the figure inside it are the same
object at two sizes, and cannot drift apart.

They are **self-contained and monochrome**. A figure's palette is built to
recede behind data, and a mark rendered in it disappears at 64px; a mark also
has to survive being dropped into a page that has never heard of `tokens/`, so
each carries its own styles inline in one ink at three strengths. A logo has to
work on a letterhead and in a favicon.

Two sizes, and the small one is not the large one shrunk. Dropping the LAND was
the obvious cut and it was the wrong one — it left a disc with a line through
it, which reads as a prohibition sign. Below 48px a 15-degree graticule falls
closer together than the pixels and turns to moire, while a coastline is a
silhouette, and a silhouette is what survives being small.

**The lock.** `assets/brand/LOCKED.json` holds a SHA-256 for the marks and for
the component that draws them, `LUMI-Globe-Field`. `check_repo.py` fails, and CI
blocks the merge, when a hash does not match without the same commit recording
the new one and a reason.

What a lock in source control can honestly promise is not that a file cannot be
edited — anyone with a checkout can edit anything — but that an edit cannot
arrive SILENTLY. It caught its own component file changing within an hour of
being written, which is the whole mechanism working.

**The ring's last hiding place.** 0.1.404 repaired the unwrap in the Python
emitter and left `projectRing` in `assets/globe/` untouched. The two are a
hand-maintained port; the golden grid holds the projection maths between them
and nothing held the clipping pipeline. So the first frame of every globe was
correct and every frame after it was not — a static check passed, a screenshot
of the loaded page passed, and the defect was visible to anyone who watched the
figure for two seconds.

A check written to guard it was **removed the same hour**: reverting the repair
left it green, because the routes it chose never reached a rotation where the
seam bit. A check that cannot fail is worse than no check, because it is also a
claim. What verified the repair was measuring the shipped demo over thirty
samples of real rotation — worst drawn-to-arc ratio 0.99 against a 1.15 ceiling
— and that is recorded as a measurement rather than a gate.

**A lane is now emitted even when it draws nothing.** A lane whose whole length
was on the far side of the first frame was skipped, so it never existed in the
document and never appeared however far the globe turned. That is the
drifting-dots defect wearing a different hat: the frame is a starting state, not
a filter.

**Two changes the owner asked for.** The axis line added in 0.1.404 came out one
release later — this figure already carries a graticule, an equator, two
tropics, a terminator edge, eight bloc borders and thirteen lanes, and a
fourteenth line through the middle of that reads as one more line rather than as
an axis. And a country in no trade bloc is now an outline rather than a fill:
on a figure whose subject is blocs, filling the rest of the world says the rest
of the world is a category, and it is not one — it is the absence of the eight.

## 0.1.404 — the ring came back, and a tilt nobody could see

**The ring, again, from a different place.** 0.1.403 unwrapped the longitudes
where a lane is BUILT. `split_at_seam` re-expresses them relative to lon0
afterwards, and returned a part spanning 376 degrees for seventeen degrees of
route — so `densify` swept the world filling the gap and the lane closed into a
ring, exactly as before, one stage further down the pipeline. Each part is now
re-unwrapped after the split, which is a no-op for every part that was already
continuous, and that is every coastline and every graticule line.

**The check that could not fail.** 0.1.403 claimed the fix was verified by
sweeping 24 rotations and measuring each lane's drawn width against the disc.
That measurement is incapable of failing: every path is clipped to the visible
cap, so its extent is bounded by the disc by construction. It reported "no ring"
about a figure full of them.

The property that works is LENGTH. A lane's projected length cannot exceed R
times its angular length, whatever produced a sweep and wherever in the pipeline
it happened. Under the old behaviour a Shanghai-to-Singapore lane drew 3.5 times
its own arc. That is now the assertion, over four routes and twenty-four
rotations each, and reverting the repair reports it in those terms.

**A tilt nobody could see.** Reported as "I do not feel the lean". Measured, the
tilt was correct all along: the pole sits 23.44 degrees off vertical, 389 units
right of centre at R=1000. The problem was that a sphere is rotationally
symmetric, so a rotated drawing of one has nothing to be rotated AGAINST — the
graticule turns with the geography and the result reads as a globe seen from
somewhere else.

A desk globe reads as tilted because you see the spindle against the stand. So
the figure now draws the rotation axis through both poles and out past the limb,
and a vertical reference through the centre, emitted outside the tilt group
because a vertical that tilted with everything else would be no reference at
all. The angle between them is the obliquity, and it is now a thing on the page
rather than a claim in a caption.

**Not a defect: the terminator.** Reported as wrong because Beijing and
Singapore fell on opposite sides of it while sharing a time zone. They do, and
they should. A time zone is a political convention — China runs one across sixty
degrees of longitude — while the terminator is astronomical and depends on
latitude at least as much as on the clock. At 06:00 on the June solstice the sun
is 12 degrees above the horizon in Beijing and 14.5 below it in Singapore, which
is why Beijing's midsummer sunrise is around 04:45 and Singapore's is near 07:00
every day of the year. The figure was right; the expectation it was measured
against was not.

## 0.1.403 — a lane that wrapped the world, and routes through the straits

**The bug.** Reported from a rendered globe: several lanes closed into rings
around the sphere as it turned. `great_circle` took its longitudes from atan2,
which returns (-180, 180], so a lane crossing the antimeridian stepped from
-178.6 to +176.1 — a jump of 355 degrees between two samples five degrees
apart. `densify` interpolates linearly in longitude and cannot know that, so it
filled the gap by sweeping the entire world. Every Pacific route did it.

This is the FOURTH time this exact failure has been introduced in this
repository, and the comment in `night_ring` already named the first three. The
check could not see it because it asked the right question about the wrong
thing: coplanarity holds perfectly for a ring whose samples are all on the
correct great circle and merely written in a representation that jumps. Lanes
are now checked for continuity in longitude as well, and reverting the unwrap
reports "jumps 358 degrees of longitude between adjacent samples".

**The routes.** A lane is no longer one great circle. `--links` takes `via`, a
list of waypoints, and the lane becomes a sequence of legs — each still the
shortest path, so the geometry stays honest at the scale it is claimed at, but
the claim is now a shipping lane rather than a line on a sphere. Shanghai to
Rotterdam goes Luzon, Malacca, Bab-el-Mandeb, Suez, Gibraltar; Rotterdam to Los
Angeles goes through Panama, which without it drew straight across Mexico.

The unwrap carries across the leg joints, and the joint point is dropped once,
so a five-leg route is one continuous ring rather than five that happen to
touch. Both are checked: a route that reintroduced the seam at a joint, and a
route that repeated its waypoint, each fail with their own message.

WHICH straits a lane uses is editorial — a claim about shipping rather than
about geometry — so the waypoints are supplied by the document. This package
ships the route maths and no routes.

## 0.1.402 — trade lanes on the sphere, and a signal that carries a real code

The globe takes `--links` and `--codes`. A lane is drawn as the GREAT CIRCLE
between its two ends, which is the shortest path across a sphere — so the
drawing and the claim are one object rather than a picture of one — and because
a lane is just a ring it goes through `_project_ring` and gets limb clipping,
seam splitting and far-side culling without a line of new code. A lane on the
back of the Earth is not drawn because there is nothing there to draw.

Weight is encoded twice, in width and in opacity, and that is deliberate rather
than redundant: the light lanes have to survive being light, and both channels
have a floor because a lane nobody can see is a lane that should not have been
in the data.

**A signal carries a real datum or it does not ship.** `references/brand.md` is
unambiguous — "a shimmer with no data under it is decoration, and decoration is
contention" — so the signal layer emits nothing at all without codes to carry,
and the check says so in those words when the guard is removed. Signals are
EMITTED, not created by the runtime: the same rule marks obey, which also means
a document with JavaScript off shows lanes carrying codes rather than lanes
carrying nothing.

They move on the same clock and under the same gates as the rotation, so
`prefers-reduced-motion` stops them where they are — leaving a legible diagram
instead of an empty one — and the off-screen gate stops them with everything
else.

**What the check had to learn.** The first version asserted that every sample of
a great circle lies on the unit sphere. That is vacuous: every (lon, lat) pair is
on the sphere by construction, so replacing the interpolation with a straight
line in lon/lat — a rhumb line, and not the shortest path at all — passed it. The
real property is that a great circle is the intersection of the sphere with a
PLANE THROUGH ITS CENTRE, and the check now measures the distance from that
plane. The rhumb line misses by 0.87 of a radius.

Three treatments of this layer were prototyped and compared before one was
chosen; the other two are not in this package and never were.

## 0.1.401 — the globe leans right, names its cities, and colours its blocs

Four additions to the globe, and one of them turned up a defect in a kind of
reasoning rather than in a line.

**The pole leans right.** `rotate(-tilt)` carried it left; SVG rotates clockwise
on a positive angle. Which way it leans is a free choice — obliquity is an angle
between an axis and a normal and has no handedness a viewer can see — and it had
shipped leaning one way since 0.1.397 **with nothing asserting it at all**. The
tilt now has a check: the group exists, the angle is the obliquity rather than
the 23.5 everyone quotes, and the sign leans right. Both mistakes fail it.

**Blocs on the sphere.** With `--regions`, the land is routed into one path per
region instead of one path for the world — the same total clipping work, because
a ring is clipped once either way and only the bucket changes. The paths carry
the SHIPPED `rg rg-<id>` classes, so one palette serves the globe and the flat
map and the two cannot disagree about what colour a bloc is. Without `--regions`
nothing changes: a field of marks should not silently gain political fills.

At full strength the eight hues buried the data — Australia read hotter than the
mark on top of it — so `.gl-rg` takes the same hue at 42% and the marks stay the
only saturated thing on the figure.

**Cities, named.** A `--cities` layer that carries visible text, which marks
never have. Text on a sphere needs three things a circle does not: the far-side
rule applied to dot and name together, a side flip so a label near the right limb
runs inward rather than off the edge, and collision culling. Labels are placed
outward from the view centre and one that would land on another is DROPPED, never
nudged — dropping is what keeps the static frame and the live frame agreeing.

**Bloc labels** carry abbreviation, membership and population magnitude —
`AFTA 10 · 0.69B` — and are hidden well before the limb, where the geography
under them is a sliver. Population is a new registry field beside `count`, since
a consumer holding the members should not go elsewhere to say how many people
they are. ASEAN's entry is 690M, not the 530M the founding-era text quotes; both
are right about their own year and a label drawn today has to be right about
this one.

**Two lessons, both about checks that agree with themselves.**

The label placement first compared boxes computed from the same constants it was
verifying. Setting the padding to zero left it green while three European names
rendered as one blot. Overlap is now measured in a browser off the RENDERED
glyphs, and it caught the real defect immediately: the estimate 0.55 em/char was
the MEAN of the shipped face, not an over-estimate of it, and real names run 0.48
to 0.62.

Then the deeper one. Placement was being decided in the earth group's own space
while the labels render TILTED — positions rotate, label boxes stay axis-aligned
to the screen, and at the obliquity a point 700 units above centre moves 280
sideways. The crowded corner of the frame is not the crowded corner of the
picture. Placement now converts to screen space first, and the dot-to-name gap is
stated on screen and converted back, because a plain offset in group space came
out at 23 degrees.

## 0.1.400 — the gate measured ink the viewport never painted

`inspect_layout.py --deliverable` called a correct document NOT SHIPPABLE on two
of its ten gating findings, and both were the same measurement error.

`inkBox` measures an SVG by `getBBox()`, which is the union of the children **in
user space** and knows nothing about the viewport. An SVG with a viewBox clips at
its own edges, so geometry outside it is not painted. The globe's plate carries a
drop-shadow, and a filter region inflates that bbox by a tenth of the viewBox in
every direction — about 50 CSS px at a figure's size. That phantom band collided
with the paragraph above the figure and spilled past the footer below it. Nothing
was out of place on the page; the ruler was longer than the thing it measured.

The box is now the intersection of the bbox with the element's own rect, which is
what a viewport paints. A correct figure pays nothing, because its ink is inside
its box already. Guarded by a planted case in `check_globe.py`'s shared suite,
written as the general property rather than the particular bug: a circle drawn far
larger than the viewBox that frames it. A filter region is one way geometry lands
outside a viewport and an oversized shape is another, and one clamp answers both.

The check also asserts its own case still overflows, so a browser that changes how
`getBBox` treats a filter cannot quietly turn this into a check of nothing.

## 0.1.399 — half of every day was inverted, and a check that swept one axis of a two-axis geometry

Two defects in the day/night terminator, both found by building a deliverable
and looking at it, and neither visible to a check that had reported 0.08% error
nine views running.

**The antipode.** The night side is a cap about the sun's antipode, and the
antipode was computed by a two-branch expression: subtract 180 when the sun is
east, reduce mod 360 when it is west. The western branch returns the sun's OWN
longitude. So for every subsolar point in the western hemisphere — half of every
day — the cap was drawn around the sun and the figure shaded its daylight. One
normalisation replaces both branches.

**The handedness.** `signed_area`'s docstring has said since 0.1.389 that its
sign is meaningless within a hair of a hemisphere, and the terminator is exactly
a hemisphere. Its sign there tracks which pole the cap happens to enclose, so
every cap centred north of the equator was classified backwards on top of the
first defect. `clip_to_cap` now takes an optional handedness, and a ring built
by `cap_point` — whose interior is on the right by construction — passes it.
Country rings, far below the ceiling, still ask as before. Mirrored in
`assets/geo/projection.js`.

**Why the check missed both.** `check_terminator_area` moved the view centre
across nine positions and held the sun at one eastern longitude on one date. The
geometry has two inputs and it swept one. It now sweeps a full day of hours and
both solstices plus an equinox, and each defect fails it on its own: reverting
the antipode reports "night should cover 90.5% of the disc and it covers 2.5%",
reverting the handedness reports "9.9% … and it covers 90.1%".

Also in this release, from the same build-and-look:

- **A globe stating a field no longer draws the registry's place layer.** Those
  four city-states exist because no shape can be filled for them, which is their
  whole job on the flat map; on a globe carrying marks they are a second point
  vocabulary at nearly the same radius. The first demo drew Singapore twice —
  once as a datum of weight 9, once as a place — and no reader could tell which
  circle was the number. Scenery still names places; a field asks with `--nodes`.
- `MARK_R_MIN` rises from 0.008R to 0.011R. Legibility only, and deliberately
  not asserted: the justification that suggested itself — a pointer target — is
  false, because `pick.js` hits on a fixed 12 CSS px radius whatever the mark is
  drawn at. Recorded in the check so the next reader does not add it.
- The trade registry names the five members nothing in the package could name.
  A panel is the intended consumer of a bloc's membership, and one that could
  name 50 of AfCFTA's 55 would print a list shorter than the count above it —
  the 0.1.398 count defect one layer down. Now graded.

## 0.1.398 — trade blocs on a map that cannot fill them, and the count that is a fact about the bloc

A second registry, `assets/vectors/regions-trade.json`, generated by
`scripts/build_trade_registry.py` from eight trade blocs. It does not replace
the geographic `regions.json`, which stays the shipped default: the blocs cover
part of the world and `check_region_coverage` wants every country in exactly one
region. The per-instance registry machinery of 0.1.395 exists for this.

**The blocs overlap, and a fill cannot.** Canada is in USMCA and in CPTPP;
ASEAN's ten sit inside RCEP's fifteen. So each record carries two lists. The
`members` list is a base PARTITION, derived here and never typed, under a rule
stated in the registry itself — smallest containing bloc wins, which is the most
specific true statement about a country, and whose eight sizes are distinct so
the rule is total. The `full` list is the real membership. The frame draws both:
disjoint fills from `members`, and one stroke-only overlay per bloc from `full`,
`display:none` until a reader selects it. Selecting CPTPP outlines all twelve
across four different fills. That is the whole product point of a bloc map, and
no amount of translucent stacking gets there without spending every contrast
floor the palette clears.

**A count is a fact about the bloc, not about the geometry.** Eight members have
no shape at this resolution — Malta, Singapore, Bahrain and five African island
states. The label says 27 for the EU while 26 shapes fill, because a count taken
from what happened to draw is a smaller and different claim than the one the
reader is owed. Now a graded invariant: the check reads the printed number back
out of the frame and compares it against the membership, and reverting it
reports "eu: the label says 26 and the bloc has 27 members".

Also in this release, each found by looking at the rendered map rather than at a
passing check:

- **`.rg-label-n` and `.rg-label-v` had classes and no rules** since labels
  shipped, so a value and a membership count set identically to the bloc name
  beside them. The same class-with-no-rendering defect 0.1.396 found on the
  globe's hover state, one file away.
- **A label at the frame edge was half-drawn.** Mercosur's name is centred on an
  anchor near the right edge, and the half outside the viewBox is simply not
  painted. Labels now clamp into the frame on an estimated width — an
  over-estimate, because the cost of over-estimating is a label a few units off
  its anchor and the cost of under-estimating is a truncated name.
- **Two anchors sat under their own point nodes**, putting a white disc through
  the middle of "AFTA" and "GCC".
- The equator and the tropics, added to the globe in 0.1.397, are now on the
  flat map too, at the same 23.44 the globe tilts by. One world, one set of
  named latitudes.
- A registry that ships now ships its palette: `tokens/region-palette-trade.css`,
  scoped under `.trade`, all four floors cleared in both themes. A bare
  `build_region_palette.py --check` walks every shipped instance, so registering
  a registry in CI is one row in a table.

## 0.1.397 — the globe becomes an Earth, and two lenses of daylight inside the night

The globe carries an axial tilt, the tropics, the equator and a day/night
terminator. **The tilt and the flattening are one SVG group transform, not a
change to the projection** — and that is a decision, not a shortcut. Touching
`unrolled()` would invalidate the 1300-sample golden grid that holds the
JavaScript port to the Python authority, and what it would buy is sub-pixel:
WGS84 flattening is 1/298, so at R=1000 the two axes differ by 3.4 units in a
2000-unit frame, and the geodetic-versus-geocentric latitude difference peaks
at 0.19 degrees. **The flattening is invisible and the owner was told so.** What
makes the figure read as a sphere is the tilt, a graticule at 15 degrees
instead of 30, and the two tropics — which sit at exactly the obliquity the
tilt uses, so one constant serves all three.

**The terminator is the same shape the clip already speaks**: night is a
spherical cap about the antisolar point, so it goes through `_project_area`
like any country and comes back cut at the limb. The sun is fixed in screen
space (owner decision) — the Earth turns under it — which has a consequence
worth stating: the night polygon's projected shape is then INVARIANT under
rotation, so the runtime never redraws it and needs no solar maths at all.

**And it drew two lenses of daylight inside the night side.** Both were
well-formed polygons, both invisible to every markup reader, and both found by
measuring rendered pixels against closed form — a great circle whose pole sits
at angular distance d from the view centre cuts the disc into a night part of
exactly (1 − cos d)/2:

- The terminator ring is a **hemisphere**, the one radius at which
  `signed_area`'s branch flips — 0.1.389 measured it and wrote it down — and
  facing the antisolar point the ring lay exactly ON the limb, leaving the clip
  to decide the winding of a curve coincident with the boundary it was being
  clipped against. It is drawn 0.05 degrees inside now: 5.5 km on the ground,
  an order of magnitude finer than the quarter-degree the solar position itself
  is good to. The terminator is drawn inside its own error bar and the
  degenerate case stops existing.
- `cap_point` returns **unwrapped longitudes**, so the ring stepped through a
  355-degree discontinuity once per circuit and `densify` interpolated straight
  through it, sweeping the whole world into a second lens. This is the third
  time `densify` has been handed a ring whose longitude representation jumps
  with nothing to tell it so.

Worst error over nine views: **13.5% before, 0.08% after**, and the new check
asserts it against the closed form by counting pixels with a ceiling of 0.5%.

**The named circles rotate.** `.gl-equator` and `.gl-tropic` were emitted and
then left out of the runtime's redraw, which would have pinned them to the
frame they were generated in while the world turned underneath.

**Read against a reference.** brila.ai's globe was opened in a browser and
measured: three.js over WebGL2, `cursor: grab`, and a drop-shadow under the
sphere. Three of its four ideas cost nothing here — a denser graticule, a
shadow so the globe floats instead of sitting printed on the page, and the grab
cursor, since this component's arcball has worked since it shipped and nothing
ever said so.

## 0.1.396 — the dots that drifted, and the audit that did not find them

**A reader found it; no check could have.** Dots drifted across the rotating
globe in the delivered demo. The cause: **the HTML `hidden` attribute does not
hide an SVG shape.** A `<circle hidden>` computes `display: inline` and keeps
its full bounding box, so every mark and node on the BACK of the sphere kept
drawing — at its orthographic position, which for a far-side point lands INSIDE
the visible disc. Measured on the shipped demo: twelve points moving every
frame, two of them `hidden` throughout while travelling straight across the
visible face.

This is the fifth time one pattern has produced a defect here, and it is worth
naming plainly: **every gate in this package reads markup, and `hidden` reads
correct in markup.** The comment at `globe_svg.py:107` asserted "`hidden` is
honoured" — a sentence that was never true. The fix is `display="none"`, a real
SVG presentation attribute that needs no stylesheet, so the JavaScript-off
frame hides them too. The new check measures `getBoundingClientRect().width` in
a browser and refuses to believe an attribute; reverted, it reports a far-side
mark "still renders 34x34px".

**The audit the owner asked for, against all three specs.** It found the split
shipped well and left six promises unkept, each now closed:

- **`--suite globe` contained zero checks.** The flag shipped in 0.1.394 and its
  contents did not, so the split spec's headline verification promise — field
  frame sanity and renderer parity — had no code behind it.
- **`.is-hover` regressed onto the globe.** Closed for regions in 0.1.391,
  reopened in 0.1.394: the runtime toggled the class on marks and nodes against
  no rule at all. Globe hover worked and showed nothing — the same defect,
  moved rather than eliminated.
- **The event vocabulary was wrong.** A mark click announced itself as
  `nodeselect`, the runtime's own header advertised a `markselect` emitted
  nowhere, and hover used a pair no spec names. A datum and a place are not
  interchangeable to a host that wants to open a panel about one of them.
- **The theme re-read was deleted with the form machinery**, leaving a canvas
  globe holding the light palette through a theme flip and a `readPalette()`
  with no caller.
- **The watchdog could not fire** outside the autorotate branch, so a dragged or
  reduced-motion globe could miss the frame budget forever without pinning; and
  `visibilitychange` resumed a globe that was scrolled out of view.
- **`lon0` accumulated without bound.** An hour of rotation reached five figures
  of degrees, spending precision on a number whose only meaningful part is the
  remainder.

**Dead weight removed from every globe deliverable**: the region layer
`globe_svg.py` has not emitted since the split, `ringsOfRegion`, and the
per-region bounding-box index — which walked every arc of every member on every
boot to build a Map whose only consumer, the hit-test prefilter, died with
`pickRegion`.

**A scoped map announced regions it was not drawing.** `embed_regionmap.py`
boots every figure from one registry, so an Asia-only map built a hidden button
per region of the *shipped* eleven — the same defect the split closed for the
globe. Registries are per-element now, which also exercises the per-element
states path that had shipped untested.

**Six phantom options are corrected in the spec rather than built**
(`class="mk"`, `--gl-mark-r-min/-max`, `data-globe-marks`, three
`createRegionMap` options, host-supplied node values): in each case the shipped
choice is the better one and the spec was simply wrong. `specs/2026-08-10-globe-map-split-design.md` §8
carries the audit, the corrections, and three findings recorded as still open.

## 0.1.395 — the registry stops being a singleton

Release 5 of 5 for the component split, and the one that delivers the owner's
"different regions and colours, different scenarios" in full.

**`build_region_palette.py --regions <path> --out <path> --prefix <cls>`.** A
custom registry gets the same six floors the shipped one gets — the floors are
the contract, not the registry — and a scoped palette: variables and class
joins under the instance's ancestor class, no second copy of the global chrome.
Two maps with different registries coexist on one page, each resolving its own
hues. `--out` is mandatory with `--regions`, because a custom palette must
never overwrite the tokens file the default registry's documents include; and
after writing, the floors are asserted against the registry that was just
written, not the shipped one — asserting the default's floors there would
bless a custom registry that clears nothing.

**Validation before colour.** No double-claimed member (the hue assignment
would be ambiguous), no member missing from the topology (a silent no-draw),
no node naming an absent region. Full topology coverage is OPT-IN
(`--require-full-coverage`): a scoped map — Asia alone — legitimately covers
less than the world, which is why `check_repo`'s coverage guard keeps
guarding the shipped singleton and only that.

**A scoped map fits its regions.** The first cut rendered Asia as a sliver
inside a world-wide viewBox — an ocean of empty graticule on either side,
exactly the reserved-space-nothing-draws-in defect the frame-fill floor
exists to catch. The map's viewBox now fits the ink; the graticule is emitted
last and clipped to it; nodes outside it are skipped. For the shipped
registry the ink box and the world are the same box, minus the empty polar
band above the northernmost coastline, which is an improvement nobody will
mourn.

`--regions` rides through `regionmap_svg.py`, `embed_regionmap.py` and
`geo_frame._load`, with the topology staying shipped throughout: regions group
countries, they do not redraw them. The globe stays on the default registry —
its subject is marks, not groupings.

## 0.1.394 — the globe becomes the field it always claimed to be, and the unroll retires

Release 4 of 5 for the component split. The globe is now one thing: a rotating
sphere carrying a field of marks. `setForm`, `unroll`, `setT`, `--form`, the
`form-*` class toggles and the `formchange`/`unrollstart`/`unrollend` events are
deleted rather than deprecated — a half-retired flag is a standing stale
promise — and `t` is pinned to 0 in the component while the shared projection
core keeps the parameter and every check that sweeps it.

**The field finally has a data path.** It never did: `hostData.marks` was
documented and read by nothing, the emitter's `marks=` parameter had no CLI
flag, and the one delivered demo showed a "field" with zero marks. The
contract is `[{lon, lat, weight, label?, id?}]`; radius scales with the square
root of the normalised weight — area encodes quantity — between a floor and a
ceiling as fractions of R. The radius rule lives in the two renderers and is
parity-held, not in tokens: CSS cannot size a canvas mark, and a knob that
binds one back end is a divergence wearing a token's clothes.

**The canvas back end draws the field and only the field.** Its regions branch
read a `state.form` the public component never set, so it actually keyed on
`view.t > 0.5` — dead divergent code the parity suite could not see, because
the canvas was never in the parity bundle. Deleted with the form. It draws
marks now, from data, with the emitter's exact radius rule.

**Renderer parity moved to the field, and covers more than it did.** The old
check compared the eleven region paths; the land path it compares now runs
every ring in the topology through the shared clip — a superset of the same
rings grouped differently — plus the three sample marks' positions. The region
side has nothing left to diverge: its runtime never touches geometry.

**The a11y layer speaks the figure it decorates.** One visually-hidden entry
per mark (name and weight — a datum is read, not operated), one button per
registry node (a place is selected). The region buttons left for the map
component in 0.1.393; the field figure that announced eleven regions it was
not showing is gone. `pickRegion` and its even-odd crossing test retired from
`pick.js` with no caller left — 30 lines of dead code in every deliverable is
not a keepsake.

`check_globe.py` gains `--suite shared|globe|map`. The t∈(0,1) sweeps sit in
`shared`, because they are the 0.1.389 winding guard and outlive the pinned
products; CI's `--python-only` invocation is unchanged.

## 0.1.393 — the region map becomes its own instrument

Release 3 of 5 for the component split. `assets/regionmap/` and its emitter
`scripts/regionmap_svg.py` are new code beside the untouched globe — the
sequencing constraint from the spec, so no commit exists in which the
repository can draw no region map.

**The map runtime touches no geometry, and everything follows from that.** A
flat map does not rotate, unroll or animate, so the frame the emitter bakes is
complete and what remains for a runtime is state: classes, values, labels,
hover, focus, the accessibility layer. Creation is synchronous; hit testing is
the browser's own pointer events on real path elements rather than an inverse
projection; and the embed block inlines the registry and NOT the 68 KB world
topology the globe must carry to re-project every frame — 11 KB against the
globe's 122. The planned render-map.js does not exist because there is nothing
for it to render; one module is what the design turned out to need.

**The registry's `anchor` and `z` are finally read.** Declared since the
registry existed, consumed by nothing: the emitter now places each region's
label at its anchor, in English from `n` or Chinese from `z` (set in the
default stack per 0.1.391's type decision), with the value beside it when the
data carries one. Each label carries `data-region-label`, the vocabulary D18
counts, so a document using this frame satisfies the label rule without
hand-authoring a legend. Label size is an attribute scaled to the frame's R —
a fixed CSS pixel size inside a 2000-unit viewBox rendered at seven effective
pixels, which is why the tokens rule now carries family and weight only.

**Two of the audit's defects die here by design.** The aria vocabulary is name
with VALUE ("Europe, 63") where a value exists — the globe's frame said
"Europe, live" while the page showed the number — and the renderer keeps it
current on setData, where the old one wrote it once and let it lie. The
one-button-per-region accessibility layer lives in this component and will
leave the globe in the next release, ending the field figure that announced
eleven regions it was not showing.

**A trap found by the component's own first test page.** The runtime applied
its host data unconditionally, so embedding without data "corrected" a frame
with baked states to all-zero within minutes of the module existing. Initial
state now comes from the markup — the classes and aria values the emitter
wrote — and host data overrides it. No data given is not data.

`check_globe.py` gains the map frame's contract: ink inside the declared
viewBox, every drawn region labelled, every emitted class bound in
`tokens/region-palette.css` (a black map is now a checked failure, not a
surprise), and the aria vocabulary — each mutation-tested.

## 0.1.392 — the shared geometry core gets its own directory, and nothing else moves

Release 2 of 5 for the component split. `assets/geo/` now holds the one library
both components stand on — `projection.js`, `worlddata.js`, `pick.js` — and
`assets/globe/` keeps what is the globe's own. `scripts/geo_frame.py` is the
Python side of the same cut: the frame assembly both static emitters will share
(load, ring decode, the clip-split-project order 0.1.389 established, the pole
close, the guard, the rounding rule, the extent), extracted from `globe_svg.py`
unchanged.

The whole release is a re-layout, and the proof is the point: the emitted SVG
is byte-identical across three reference views (both forms, three values of t),
the 1300-sample golden grid is untouched, and the full browser suite — port
parity and renderer parity included — runs green on the moved tree. A re-layout
that cannot demonstrate byte-identity is a rewrite wearing its clothes.

## 0.1.391 — the split is decided, the palette becomes usable, and Chinese type gets its honest answer

**The one-figure-two-forms decision is reversed** (owner directive, 2026-08-10 —
the documented case is the audit of the first delivered demo, recorded in
`specs/2026-08-10-globe-map-split-design.md`). The globe and the region map
become two components, separately designed, developed and verified, each
configurable per instance. The audit found the coupling was where every defect
lived: one of the two forms never had a data path at all (`hostData.marks`
documented, read by nothing), `setForm` toggled classes no stylesheet defines,
the canvas back end branched on a state the runtime never set, and the unroll —
the feature the coupling exists to serve — was unreachable, because nothing in
the package emits a control and the first real deliverable authored none. The
split lands over four further releases; this one ships the spec and the two
decisions that are independently useful today.

**`tokens/region-palette.css` ships the bindings, not only the values.** The
variables shipped for three releases with no rule joining them to the classes
the emitters write, so any document that did not hand-copy ~90 rules drew every
region in the UA default — black — and every metric passed, because no check
reads rendered colour. The generator now emits, beside the hues: the `.rg-<id>`
fill and stroke bindings, the state classes (`.is-out` and `.is-partial` take
the standing status colours deliberately — they are status, not identity),
`.is-hover` (toggled by the runtime since the globe shipped, defined by nothing,
so hovering worked and showed nothing), `:focus-visible` (the first demo shipped
`outline:none` on a `tabindex="0"` element), and the `--gl-*`/`.gl-*` figure
chrome the canvas back end has read since it was written and no host ever
defined. The fixture's private copy of the join is deleted — a reference
implementation should not need a private companion to render. `.is-live` is the
unmarked state, and the file says so rather than shipping a rule that restates
the binding above it.

**Chinese deliverables use the default stack** (owner decision). No CJK face is
vendored and none will be: a comparable-quality face is one to two orders of
magnitude larger than the Latin pair. The embed rule is scoped to the faces the
package ships, and the design rules now state the fallback chain and its cost —
CJK rendering depends on the reader's machine — instead of keeping a sentence
that could not be kept for half the documents this package exists to produce.
This also unblocks the rendered Chinese fixture that item 2 filed under a
licence question; building it is its own change.

## 0.1.390 — the backlog, and the instruments that could not fail

The seven items in the tracked ideas backlog, in the order it set. What they had
in common turned out to be sharper than the backlog knew: **five of the seven
were not missing features but missing verification**, and three of them were
guards that had been written, documented, and never wired.

**Item 3 · A suite that could not tell a working checker from `return "ok"`.**
Thirteen of eighteen design verdicts and four of seven prose verdicts read `ok`
on BOTH fixtures. Ten of them could not be given a failing case in
`deck-broken` without destroying it as a worked example — four are document-WIDE
prose properties (every sentence the same length, every title the same shape)
that cannot be confined to one labelled page — so `deck-degenerate` is a third
fixture whose only job is to fail. Coverage is now **computed**: the checkers
emit their targets, and `check_fixtures.py` refuses a graded verdict no fixture
fails. 30 of 30 today, against 8 of 18 before.

Three defects in the checkers, all found by using them. `KNOWN_FLAT_CLOSURES`
documented a two-way lock whose second half **was never implemented** — the
pairs seen were collected into a variable nothing read. The flat-segment probe's
loop sat OUTSIDE the per-path loop and examined one path per frame of twelve. And
`inspect_layout --json` printed a note to **stdout ahead of the JSON**, so any
deliverable that declares no `data-geometry` emitted a stream no parser could
read — which the conformance harness had been recording as "layout emitted no
parseable report", a defect in the deliverable rather than in us.

**Item 5 · Two viewports the rules name and nothing ran.** `laptop` and
`16x9-hd` were absent from the default list, and widening that list would still
not have reached a deliverable: the declared-geometry branch narrowed to two
geometries, which is where they were actually being lost. Running them found
`footer_wrap` firing on all 18 pages of the PASSING fixture at 1920×1080 — the
probe compared a rect in **device space** against `parseFloat(lineHeight) || 14`,
and `line-height: normal` does not parse, so a good footer measured 22.5 against
a threshold of 22.4. It counts line boxes now, and `deck-degenerate` carries a
real two-line footer so the fix is proven to still fire.

**Item 1 · M6, M2, M1 — the three metrics standing behind a fact red line.**
Half the rubric's prose metrics had no code and three of the six stood behind
"every number carries its source", so a deliverable could break all three and
pass every check shipped. The window each one measures in is now stated in
`writing-rules.md` §4 rule 6 — the page for an ordinary figure, the block for a
range, because a range must trace to a SINGLE source — and a new `source-marker
parity` guard holds the script's vocabulary to the rules'. The window was
settled by measurement, not preference: a block window scores a correctly built
deck at 0%. **M1 reports and never gates.** Its predicate is a proxy for a
judgement, and a proxy that gates is one authors write toward; the first cut
scored a well-formed deck at 18.8% because it read only digits, which is exactly
the line a reviewer learns to skip.

**Item 2 · The Chinese half had rules across four sections and machinery for
none of them.** Phase 1, the parity guard, went first because it is a guard
rather than a feature: it closes the drift channel before there is new code to
drift. Phase 2 gives Chinese documents the banned-phrase list and the
punctuation pass. A Chinese document used to come back UNMEASURABLE, and that
was the real reason this checker was English-only underneath the docstring
saying so — the word splitter needs spaces. Phase 3 was filed as blocked on a
font licence because a fixture has to render; that is true of the RENDERED half
only, and `check_prose.py` renders nothing, so a Chinese prose fixture pair
ships now and the licence question is unchanged for anything a browser must
open. M3, M7 and the de-translationese pass are recorded as **not mechanized**
with reasons: the first two need a per-document term registry this package does
not ship, and inventing one would be a rule nobody wrote.

**Item 4 · The half that iterates had no memory.** Six dimensions, a protocol
where a divergence of two forces a retrospective, and not one stored score —
every number lived as a sentence in a release note. `reviews/scores.json` and
`scripts/review_scores.py` store and print the series, backfilled from the two
rounds the changelog records as prose. The schema has **no free-text field**,
which is the engagement-fact defence rather than an omission, so an unknown key
is an error. The protocol's own rule against self-scoring 5 before a reader has
is enforced in the tooling, because a number series invites optimising it.

**Item 6 · The capability tier was the one registry claim nothing verified.**
Install path, docs URL and CLI probe each carry a verification field and a waiver
when unverified. `capability` had none — and it is the claim that decides whether
an agent may call a deliverable *verified*. Running every probe on this machine:
one of twelve is installed. So `capability_verified` is true for `claude-code`
alone, eleven waivers name what is unconfirmed, and each is **published in the
install note** rather than kept in the registry. The `files` tier stays, marked
unpopulated: it describes a real shape, and the way to fill it is to exercise an
agent, never to reclassify one from reading its documentation.

**Item 7 · A board reporting one sample as though that were the method.** An
unreferenced results directory sat on disk — a second Claude Code run nobody had
scored, which is the repeat the board most needed. `scored.update()` made a
repeat OVERWRITE its predecessor, so "n=1 per agent" was a property of that one
line and not of the harness. Repeats accumulate now and a cell carries its
spread: `2 runs, all fail` is a different claim from `2 runs UNSTABLE`. And
absence has two kinds — six rows are a machine away, four can never answer a CLI
probe at all, and printing them identically made ten pieces of pending work out
of six.

**And an eighth thing, found by looking at the sheet.** With the geometry matrix
widened, the contact sheet showed figure 9 of the PASSING fixture as four solid
black rectangles — at every geometry, for as long as that figure has existed.
`globe_svg.py` emits `class="rg rg-europe is-live"`, `region-palette.css` ships
`--rg-europe` and its stroke and wash, and **nothing in `tokens/` joins the
two**, so every region fell back to the UA default. `D18_region_labels`,
`D5_drawn_share` and `D5_figure_parity` all passed, because no check in this
package reads rendered colour. Convention 8, again, and the third release
running that it found something the instruments could not.

The fixture paints its regions now, generated from the palette so a new region
cannot leave a black shape. **Whether `tokens/` should ship that binding itself
is left open**: `design-rules.md` §1 puts painting on the document, but a
document currently has to write eleven regions by hand to draw a region map, and
that is the shape of a rule mandating an asset the package does not ship. It is
a design decision, so it is recorded here rather than taken.

Three things the backlog proposed and this release did not do, all recorded
rather than dropped: a Chinese fixture anything must RENDER still waits on a
font licence; one mutation of the spherical clip — a run linking to its own
entry instead of the next run's — produces a result too small to trip the area
invariant and nothing catches it; and `M1`'s proxy scores a well-formed deck at
43.8%, which is information about the proxy as much as the deck and is why it
reports rather than gates.

## 0.1.389 — winding carried through the clip, and the two defects the eye found after the checks went green

**The clip moved to the sphere, which is the whole change.** 0.1.388 recorded
three flat closures and one renderer divergence under one diagnosis: the limb
walk picks the arc that is shorter BY INDEX, and the correct arc is the one that
keeps the polygon's interior on the correct side. That diagnosis was right and
incomplete, and implementing only what it names makes the figure worse — a
prototype of exactly that took the flat closures from one per frame to **114**.

The half that was missing: **the projected cap is not a closed curve.** The
renderers sampled the cap in azimuth and projected each sample, and `unrolled`
wraps longitude into `(-180, 180]` before mixing in the plane term, so the
sampled boundary jumps the full width of the seam twice at every `t > 0` — 511
units at `t=0.25`, 1004 at `t=0.5`, against `R=1000`. Every flat closure
recorded in 0.1.388 was one of those jumps. The index-shortest rule was not
merely wrong; it was **accidentally suppressing a second defect** by rarely
walking far enough to meet one.

So the clip happens before projection now, on the sphere, where the cap is a
circle in azimuth with no seam in it. `clip_to_cap` closes a ring along that
circle in the ring's own winding and **links its runs to each other** rather
than closing each on itself. The direction is derived, not chosen: the topology
carries real winding — of 278 rings, 277 score positive by signed spherical area
and the one negative is South Africa's second, the hole that is Lesotho — and
azimuth increasing traverses the cap with the same handedness, so a positive
ring walks forward and a hole walks back. It depends on no sampling, which is
why both renderers now make the same decision and the recorded divergence is
gone.

**That measure must never be applied to the cap itself.** Its branch wraps at a
hemisphere: a cap of 91 degrees scores negative where one of 89 scores positive.
The visible cap is larger than a hemisphere for every `t > 0`, so deriving its
handedness from its own area would have inverted the walk across the entire
animated range. Written down in the function, because it is invisible until `t`
leaves zero.

`_pole_close` was restricted to `t=1` and measured against `x = cx ± R`. Both
were symptoms of an unmodelled boundary: at `lon_rel = ±180` the sphere term
vanishes at every latitude, so **the seam is a pair of vertical lines at
`x = cx ± tR`**, and a pole is a point on the sphere and a segment at
`y = cy ∓ R(1 - t/2)`. Both are exact, both are real at every `t > 0`.

**Two defects survived every check and were found by looking.** The checks went
green, the recorded entries were removed, and the contact sheet showed
Antarctica painted over the entire disc at `t=0`. Natural Earth closes it along
the `lat = -90` edge of its rectangular source map, so 181 of its 433 densified
points are a pole artifact; where the cap passes through the poles they evaluate
to `±6.1e-17` and read as interior. A point ON the boundary is not INSIDE it.
Then the same figure at a Pacific-centred view filled again, for an unrelated
reason: two runs meeting exactly at that artificial break, and a guard that read
a zero-length arc as a full wrap. Both produce a closed path whose every point
lies on or inside the cap with its winding intact — **which is to say both
satisfied all six invariants written that morning.** Convention 8 is not a
suggestion.

The seventh invariant is the one that would have caught them: **a clip can only
remove area.** A closure that walks the whole cap returns 6.2965 sr from a
0.2985 sr input. Every invariant here was mutation-tested — the fix reverted,
the check confirmed to fail — because a metric with no failing case is the
defect this release found in its own checker.

**Three defects in the checker, all found while using it.** `KNOWN_FLAT_CLOSURES`
claimed a two-way lock — a fourth fails, and so does fixing one without removing
its line — and **the second half was never implemented**: the set of pairs seen
was collected and never compared against anything, so all three could have
healed in silence. The flat-segment probe's loop sat OUTSIDE the per-path loop,
so it read whatever the last path left behind and examined one path per frame,
of twelve for the region layer. And the JS land layer was drawn without its
`view`, so no closure and no guard ran on it at all.

`geo_projection.limb_walk` took the same shorter arc and now takes the winding.
`build_geography.py`'s eight hand-authored rings have accidental winding —
`australia` and `maritime-se-asia` score negative with no hole to justify it —
so the globe normalises them; both come back geometrically identical, which
confirms the static assets were never affected. The canvas back end closed a
clipped fill with a bare `closePath`, a chord straight across the sphere, while
the SVG side walked a boundary; it shares the clip now. Its densify cache was
keyed on arrays `splitAtSeam` allocates fresh every frame, so it never once hit
and grew unboundedly at 60 frames a second — removed rather than repaired.

Recorded and not fixed: the projection **folds** at intermediate `t`. The visible
set admits a strip of the far side that maps back over the front, so at `t=0.5`
content is drawn out to radius 90.1 while the curve everything is clipped against
sits at 76.6–79.3. `invert` has always documented this from the inverse side; the
forward consequence had not been written down. Moving the threshold to the fold
crease changes `unrolled`'s visibility flag, which regenerates the 1300-sample
golden grid — the only thing holding the JS port to the Python — so it is its own
change. `specs/2026-08-10-winding-clip-design.md` carries the measurements.

## 0.1.388 — the runtime reaches the deliverable, and the closures that only a filled figure shows

**0.1.387 shipped a component no deliverable could run.** Seven ES modules,
verified over HTTP in a harness, and a demo deck carrying a static frame and no
JavaScript at all. A deliverable is opened over `file://`, where the browser
refuses ES modules as cross-origin, so `<script type="module" src=...>` there
does not merely break self-containment — it does not run. There was no inlining
path and the gap was not visible from inside the repository, because everything
here is checked against markup.

`scripts/embed_globe.py` closes it: the modules concatenated in dependency
order, the geometry as JSON, one call, no fetch and no module graph. Its
`--check` refuses to emit a block containing an unresolved import, a surviving
export, a dynamic import or a fetch, and refuses a duplicate top-level
declaration — `projection.js` and `controls.js` both declare `D2R`, correct as
modules and a SyntaxError once concatenated, which in a deliverable shows as a
still figure and one line in a console the reader never opens.

**Form and t were bound together and should not have been.** `setForm('regions')`
forced the flat map, so a document could not have the figure this component
exists for: a turning globe with its trade regions coloured. `form` now selects
which layer is painted and `t` the geometry, and rotation depends on `t < 1`
rather than on which layer is showing.

**The accessibility layer relied on the host to hide it.** A deliverable that had
not been told to style `.gl-a11y` got eleven bulleted buttons under the figure.
A visually-hidden element carries its own hiding.

**Closures that cut straight across instead of following the boundary.** Fixed:
the pole-edge close fired on the globe, where the boundary is a disc and not a
rectangle; the limb walk ran from the wrong end, so its first point sat beside
the start of the run instead of beside the end; runs were cut between samples
rather than exactly on the boundary, so the walk could not match them — the same
failure `build_geography.py` recorded when it was written; and the two renderers
rounded coordinates by different rules, Python half-to-even and JavaScript
half-away-from-zero.

**Two defects remain, both recorded and both measured.** The limb walk picks the
arc that is shorter BY INDEX, and the correct arc is the one that keeps the
polygon's interior on the correct side — a winding question, not a distance one.
Where they differ the fill spills across the polar cap. `check_globe.py` carries
the three flat closures and the one renderer divergence this produces as named
exceptions, so a fourth fails and so does fixing one without removing its line.
Carrying winding through the clip is the standard spherical polygon-clipping
problem and it is its own change.

**A new check, because nothing here could see a filled defect.** Every gate in
this package reads markup, and a band across a globe is a correctly-formed path.
`check_globe.py` now looks for long perfectly horizontal segments: after
projection a parallel is a curve, so a run of constant y is a closure that took
a straight line. It is also what found the three that remain.

`check_design.py`'s `token_blocks` kept the last `:root` block and dropped the
rest, so any document appending `tokens/region-palette.css` lost its whole token
block and reported UNMEASURABLE. Blocks accumulate now, the way CSS does, and
`d4_palette` reads them separately because it strips them by verbatim match.

## 0.1.387 — the globe: region hue by owner directive, labels carry identity, and the mark kept apart from the map

**A world figure that states data has to be generated from data.** Two reference
sites were reverse-engineered before anything was written. Both run the same
engine; their methods are opposite. One generates its geometry at runtime from
GeoJSON, the other loads a model authored in a 3D tool. A figure carrying a
number must be the first kind, because changing the number has to change the
picture without reopening a modelling tool. Neither library fits a
self-contained deliverable — half a megabyte compressed — so the geometry, the
projection and the renderer are this package's own, in the standard library and
in vanilla modules.

**Hue encodes region identity, which is the single exception to one colour one
meaning.** An owner directive, and it is safe only because these hues are
declared to carry no data meaning, exactly as `light_ramp` already is. Two
proposals were made and rejected on the way, and both are recorded because the
numbers are the reason:

* an 8-hue ceiling. Rejected: the map layer needs more regions than that.
* a ΔE00 floor of 20 over *all* pairs. Unsatisfiable at every N — the best
  achievable is 18.1 at N=8 and 6.8 at N=20. The floor now binds adjacent pairs
  only, and the label rule covers the rest.

A four-band construction was built, measured clean, and then withdrawn on
looking at it: it satisfied the adjacent floor while putting three of eleven
regions inside one narrow window, so Europe and Southeast Asia measured ΔE00 5.0
apart and rendered as one colour on the same map. Even spacing with a
max-separation assignment gives 12.0 over all pairs, 23.0/20.8 between adjacent
ones, and needs no constraint on the registry at all. **Adjacency counts regions
within 1500 km as well as regions that share a border**, because an ocean strait
is not a visual separation — Europe and North America face each other across 300
km at Greenland and the first version gave them the same hue.

**Every coloured region carries a label or a legend entry, whatever the hue
count.** At the theoretical maximum separation of 90 degrees, deuteranopia
collapses two adjacent regions to ΔE00 9.6 and protanopia to 8.5, and a real map
runs at 60 or less. Hue separates neighbours at a glance; text carries identity.
D18 checks for the text and never counts hues, because a threshold is exactly
what the measurement does not support.

**A canvas is invisible to every gate this package owns.** `d5_drawn_share`
counts a figure as drawn only if it holds an `<svg>`, `d5_figure_parity` and
`d17_export_weight` read markup, and `inspect_layout` cannot see inside one. So
the deliverable renderer emits SVG and the runtime mutates that markup rather
than replacing it: the file on disk is a complete no-JavaScript fallback, the
gates can still read the figure, and a screen reader's tree does not churn under
animation. The canvas back end exists for pages where no gate applies.

**Two geographies now ship and they disagree about where a coastline is.** The
hand-written two-degree coastlines are a *mark*; Natural Earth 110m is a *map*.
A document may use either and must never place both in one view. Re-deriving the
coarse set would change the shipped cover mark byte for byte, so it is deferred
with its own retrospective.

Nine defects were found only by putting the thing on screen, and none of them
was visible to any metric when it was found: a renderer that wiped the hover class sixty times a
second, a drag with the longitude sign backwards, an unroll that never arrived
because it eased asymptotically, a viewBox that stayed square while the map went
2:1, clipped rings closed with a chord instead of along the limb, and a form
switch into an empty map because the runtime cannot create markup it was not
given. And three separate causes of a line drawn across the whole flat map: the
two inserted seam crossings landing on the same edge because lon0+180 wraps to
-180; source vertices sitting exactly on the antimeridian, which has no side, next
to a neighbour at 177.99; and a last-piece/first-piece join that is right for an
ordinary ring and wrong for one that wraps the world. Fifteen such segments
became one. CLAUDE.md 8 governs, and it earned its place again.

**One defect is open and recorded rather than tolerated quietly.** A subpath in
the oceania region still starts on one edge of the flat map and continues to the
other, drawing a hairline across the equator at t=1 and nowhere else. No oceania
ring spans the seam, so the cause is not the seam split and is not yet known.
`check_globe.py` measures the class of defect and carries this one instance as a
named exception, so a second one fails the check and fixing this one also fails
it until the record is removed. Reproduce with
`scripts/globe_svg.py --form regions --t 1`.

Export weight, corrected against a measurement rather than a guess: a globe page
does **not** move D17 much. D17 counts polygon points and `<path` ELEMENTS, and
the globe is about a dozen elements carrying very long `d` strings — a demo deck
with two globe figures reported 14 nodes. The weight is real and it is in bytes,
not in that metric: a static globe frame is 45 KB and a flat region map 68 KB,
integer coordinates included. Say the file size; D17 will not say it for you.

## 0.1.386 — a viewBox that does not parse is a defect, not an absence of one

**A drawing whose viewBox the browser cannot read now fails the run.** Three
numbers instead of four is legal as an attribute and meaningless as a value: the
browser discards it and lays the drawing out against a box nobody chose. Found
while building an internal document, where a six-row figure rendered three rows
and left half a page empty — with every check green, because the clipping probe
added one release earlier read the unparsed box as *nothing to measure* and
skipped it silently. That is the same shape as the defect it was written to
catch, one level up: the probe could not tell a drawing it had checked from a
drawing it had given up on. Tenth `--deliverable` gate, with a planted case in
the broken fixture so it has failed once before anyone trusts it.

The lesson generalises past this probe and is worth stating: **a check that
skips is not a check that passed.** Every `continue` in a probe is a claim that
the thing skipped was not a subject, and that claim needs to be true.

## 0.1.385 — deliverables leave the package's own directory, and the sheet's figure ceiling stops contradicting the figure rule

**A deliverable lands in the reader's workspace, not wherever the input happened
to sit.** The default had been the input file's own directory since the export
axis was written, which is fine for one person working on one document and wrong
for everything else: several agents working at once, several people sharing a
machine, and — the case that found it — an input that lives inside the package,
which put finished client documents in the skill's own install tree. The default
is now one named place under the user's own documents folder, the same place on
every platform this package claims, and **the agent asks before creating it**.
Two things deliberately do not change: an export still lands beside the document
it was made from, because a deliverable's HTML and PDF belong together, and a
directory the user names still wins. A shared folder does put one new obligation
on a filename — it now carries its own identity, name and version, because two
documents that share a stem no longer merely sit side by side.

**The portrait figure ceiling and the figure-aspect rule had been contradicting
each other.** §4 says a full-width A4 cell is about 0.85:1 and asks for a drawing
built to that shape. The sheet's own `max-height` capped a figure at 52svh, which
in a 682px column means no drawing under about 1.17:1 can render at all without
being clamped short and pillarboxed. So the rule asked for a proportion the
tokens forbade, and the best page in the first handbook designed for the sheet
sat exactly on the cap. The ceiling now clears the cells it has to hold. It is
still a ceiling and not a target, and the page box remains the real bound —
`--deliverable` fails a page that exceeds it. *Measured by redrawing every figure
of that handbook to the shape §4 asks for: twenty-one drawings that had run 1.18
to 2.80:1 in cells of 0.78 to 1.10, filling 43 to 82 percent of their cell and
leaving empty bands of 12 to 35 percent, now sit within a few points of their
cell and fill 80 to 98 percent of it, with bands of 2 to 9. The redraw is the
thing §4 already prescribed; what had been missing was permission to land it.*
The redraw also confirmed the rule's own wording about how: a figure that is
already a vertical stack does not get taller boxes, it gets **another line of
real content per row** — a criterion, a consequence, a worked example. Stretching
the chrome would have hit the same number and taught the reader nothing.

**An unknown genre is now unmeasured rather than quietly graded as sales.** The
share probe read `data-genre` with a pattern that accepts any word and checked it
against nothing, so a misspelling scored a training handbook against the sales
target and said nothing. It now grades only a genre the package declares and
reports the rest as not measured. `internal` gained the entry it had been falling
through, and the help text for `--deliverable` caught up with the ninth gate that
shipped in 0.1.384.

## 0.1.384 — the caption found its figure, the table stopped stretching, and the sheet was asked to carry more than the slide

One review of the first handbook designed for the sheet, four findings. Three
were mechanical and one is a rule the package did not have.

**A caption centres on its figure.** §4 had said the caption aligns with the
drawing's left edge so the eye returns to where the figure began — a reasonable
rule that nothing measured, and that the shipped CSS had never implemented. The
caption aligned with the *cell's* left edge, which is the same edge only while
the figure's box is unclamped; the moment `max-height` bites, the drawing is
pillarboxed to the middle of its box and the caption stays behind at the margin.
The rule now says the caption block centres on the drawing, and a probe reports
the offset between the rendered caption's centre and the figure's ink, so the
next divergence is visible rather than inferred. One boundary comes with it: a
drawing whose ink is not centred inside its own viewBox cannot be aligned by
CSS at all, and gets redrawn.

**A table keeps the row height its content asks for.** A table in a centerpiece
cell was given the cell's height and distributed it across its own rows, capped
only for tables of three rows or fewer — a threshold that appears in no
retrospective and was never argued. Stretching table rows is the package's own
canonical example of satisfying a measurement without improving a page: it is
why the 82 percent fill floor was withdrawn in 0.1.340. It should not have
survived as a mechanism after being named as a defect. Tables now sit at their
natural height and the cell's slack stays in the cell, which is an honest empty
band rather than a disguised one.

**A cell holding a grid aligns to the top, and a drawing that leaves its own
viewBox is now a gate.** Two findings the table change surfaced. With the stretch
gone, a centred table put 280px of nothing between the support line and the header
row — read as a missing section on a page, and as a missing question on a scoring
form the reader writes on — so a cell holding a table starts under the title and
lets its slack collect at the bottom, where it is room to write. And measuring
figures for the caption rule turned up three drawings whose text ran past the
right edge of their own viewBox: a root `svg` clips there, so those sentences were
never rendered at all, with no overflow, no collision and no spill for any other
probe to see. That is the defect CLAUDE.md rule 8 names as the reason a person has
to look at the render, and it is decidable, so it does not need one — it is the
ninth `--deliverable` gate.

**The stat band ships its own rendering.** `.band` carried a cross-axis rule and
no `display` at all, so every document that used one re-invented the box —
the orphan-role failure this package has now recorded four times. The base is
column auto-flow, because a band carries as many tiles as its page has data and
a fixed column count breaks the first page that disagrees.

**A page on the sheet carries more than a page on the slide.** New rule, and the
first per-geometry statement in this package about *content* rather than
composition: an A4 portrait content page carries a second content block beside
its centerpiece — what to notice in the figure, the steps, the caution, the
worked example — and at least one highlighted key point. It is a floor on the
page's blocks and deliberately not on the support line, which stays at one to
three sentences; a page that cannot hold both becomes two pages, because the
sheet is fixed and type is never nudged to make room. *Provenance: the first
handbook designed for the sheet gave nine of twenty-one content pages a second
block and left the other twelve running a 24 to 33 percent empty band under the
figure. Its reader asked why the printed page said less than the projected one.
The layout rules had all been applied; none of them was about how much a page
should say.*

Also: the vertical layout family now states which of its rows absorbs the slack,
because the one whose flexible track sits in the *middle* had been picked for a
figure-led page and put the whole sheet's leftover height between the band and
the drawing. And two files still counted the design metrics as D1–D16 after D17
shipped.

## 0.1.383 — three things the sheet taught, once a document was actually designed for it

**The visual share is graded at the geometry the document declares.** It asked
"is this render A4", which was right while portrait was always a second edition
and wrong the moment a handbook declared the sheet as its own stage: the
training target was reported and never applied on the only geometry that
mattered. It now grades the declared one and reports elsewhere.

**Stacked cells centre on the sheet.** Side-by-side cells top-align so a reader
can cross between them; on the sheet those same cells are stacked rows, where
there is nothing to cross and the rule only pushed every page's slack to the
bottom edge. Measured on the handbook: the boundaries page carried a 37 percent
empty band and the glossary 49, which centring took to 20 and 26.

**A figure is drawn for the geometry it will sit in**, and §4 now says what the
cells actually are: about 2.5:1 full width on the slide and 0.85:1 on the sheet,
1.3:1 and 1.0:1 in two columns. A 1.5:1 drawing in a 0.85:1 cell fills a little
over half its height however it is scaled. *Provenance: the first handbook
designed for the sheet drew its figures at 1.4:1 to 2.2:1 and ran a 24 to 39
percent empty band against 5 to 27 on a landscape deck built the same week.
Redrawing one figure's four gates from a row into a two-by-two took it from 47
to 76 percent of its cell, which is the fix the rule now names: portrait figures
stack what landscape figures place side by side.*

## 0.1.382 — the window stopped deciding the design, and the declaration reader stopped reading its own documentation

Producing the first document actually designed for the sheet put the 0.1.380
portrait work under load, and it found four defects in an hour. Every one of
them was invisible until a portrait deliverable existed.

**The type scaled with the reader's window while the page did not.** The
display tiers were `clamp(min, Nvw, max)`, written before the page became a
fixed box. With a `zoom`-scaled stage, `vw` resolves against the window and the
box does not move, so one document set its titles at one size on a laptop and
another on a wide monitor. Measured on the handbook: the cover's display type
nearly doubled between the sheet and an 1800px window, and its ascenders
landed on the wordmark. The tiers are now **fixed per stage** — the values the
old clamps resolved to at each design geometry, so nothing moved at the
geometry each was drawn for — with the portrait block carrying the sheet's own
set. `zoom` stays viewport-relative, because scaling the whole stage to the
window is the one thing that should follow it.

**The reserve and the datum asked the window which geometry it was.** Both read
`window.innerWidth >= window.innerHeight`, so a portrait handbook opened wide
was told its released reserve was overspent and its released datum was lost.
They now read the document's declaration, which is the thing that decides
composition since 0.1.380.

**The declaration reader read the stylesheet's own documentation.** 0.1.379
matched `data-geometry` in the CSS *selectors*; 0.1.381 anchored on the `<body>`
tag and then matched the worked example inside a token file's *comment*, which
graded a portrait handbook as landscape. Both readers now strip style blocks and
comments before looking, because what is left is markup. Second instance of one
defect, and this note is here so there is no third.

**The cover typeblock shipped a zero gap under leading of .92.** Display glyphs
stand taller than their line box, so the title's ascenders reached the wordmark
above them: a 3px overlap on the cover and the closing, which the collision
check catches and a reader sees as a smudge. The typeblock now carries a 12px
gap, and the workaround a deliverable had added locally is deleted.

## 0.1.381 — the apparatus exemption, declared rather than inferred; and a scope the audit did not know

Two owner decisions from the 0.1.380 review, both closing a gap that had already
made a real deliverable work around a check instead of satisfying it.

**A reference page is exempt from the visual-share target, and it says so.** A
glossary, a scoring page, a boundaries page and a how-to-use-this-deck page are
reference the reader returns to rather than claims the deck advances; asking
them to carry a figure produces decoration, which is what every rule in §4
exists to prevent. They now carry `data-role="apparatus"` and drop out of both
halves of D16.

**Declared, never inferred** — that is the whole design. An inferred exemption
is the escape hatch that empties the metric; a declared one is auditable, and
the pages that claimed it are named in the report. The test is the claim: a
content page advances one and owes its visual block, an apparatus page carries
none and owes nothing. A page that merely failed to earn a figure is not
apparatus. The share carries **a ceiling of about one content page in five**,
because past that a deck has stopped arguing and become a handbook — reported,
never gated, like the rest of D16. Both fixtures exercise it in opposite
directions: the passing one holds a prose-only page that declares itself and
must not be listed, the broken one keeps an undeclared prose-only page that
must.

**`.tag` joins `.no`'s shipped scopes in the consistency audit.** `tokens/` has
shipped `.tag.no` — the refused status chip — since 0.1.375, while the audit
knew only `.swap .no`, so a document using the chip was reported as inventing a
rendering it had not. A scoped audit that does not know every scope the
stylesheet declares manufactures the split it exists to find. The evidence that
this mattered: the 0.1.379 deliverable worked around the finding by choosing a
different chip, which is a check shaping a document rather than measuring it.

## 0.1.380 — one document, one geometry; and the blend mode that cost ten times the render

A reader opened the A4 edition of a landscape sales deck and found five defects.
All five were real, four of them had one root cause, and the fifth was measured
rather than guessed.

**A deliverable is designed for one geometry, and it says which.** The two
stages were window-shape media queries, so a landscape deck in a tall window —
or exported at A4 — silently became a portrait composition nobody had designed:
dead half-pages, a figure starved to 188px in a 682px column, and a footer
wrapped on all 31 pages. None of it was visible at the geometry the deck was
built for. The stage now hangs off `<body data-geometry="landscape">` or
`"portrait"`, the portrait composition applies because the document *says* it is
portrait rather than because a window happened to be tall, `inspect_layout.py`
grades the declared geometry, and `export_pdf.py` **refuses** the other one. The
genre still picks the default — sales, marketing and consulting lead landscape,
training leads portrait — and **when a request settles neither the genre nor the
format, the skill asks before generating.** That is the one question worth a
round trip, because the answer changes every page. A second geometry is a second
*composition*, in its own file.

**The footer wrapped because the page frame shipped nowhere.** `.page` had no
rule in `tokens/`: every document invented its own `position`, `display` and
padding, and a document writing `padding: 44px 92px` overrode the sheet's 56px
margin, leaving the footer 610px where it had 682. The fix is not a smaller
font, it is shipping the frame — the same defect as the missing
`.foot { display: flex }` of 0.1.366, and the footer's own type now ships too
(`--fs-foot`), because "footer terms" has been an audited role since 0.1.350
while every deck declared its own size. **A wrapped footer is the eighth gating
finding**: it is furniture overflowing its frame, which is decidable.

**Two portrait rules were reserving space the content did not have.** The
collapsed split used `minmax(0,3fr) minmax(0,2fr)`, so a short first cell left a
dead band measured at a third of a sheet; the cells now hug their content and
the centerpiece absorbs the slack. The portrait figure cap rose from 36svh to
52svh, where a wide drawing had been rendering at a quarter of the page. The
short-narrow and short-height media queries were removed outright: they predate
the zoom stage, and a small window now shows a smaller page rather than a
narrower one, so collapsing its columns answered a problem the stage had already
solved.

**A figure's name holds one line.** 14 of 17 captions wrapped at A4 and 7 of 17
at 1280, because nothing bounded the name. It is a ceiling, not a target — about
100 characters on the slide, about 60 on the sheet — and a name that overruns
gets shortened, never set smaller. `inspect_layout.py` counts wrapped captions.

**The visual-share target follows the genre** (owner directive): about half the
content area for sales, marketing and consulting, where the page argues
visually; about a third for training, where a learner needs the words beside the
drawing. The document declares its genre and the checks grade against that
number. Both remain review triggers, never floors.

**And the PDF: `mix-blend-mode: multiply` cost an order of magnitude.** A 513 KB
31-page export took 4515ms to render; removing the blend on five opener pages
alone brought it to 448ms. One blended element forces the reader to composite the
whole page. Baking the ground's alpha per tier and cutting its node count by 44%
changed the file size and nothing else measurable, so the fix is the mode, not
the geometry: on the lime field the ground darkens the field, which is a colour —
its strokes take the field's own foreground — and the look is identical.
`check_design.py` gains **D17, export weight**, reporting blend modes, filters
and vector nodes, and `export_pdf.py` warns when a PDF it just wrote carries a
blend mode.

## 0.1.379 — the four-agent review of 0.1.375–0.1.378, closed

The owner ran a four-way review over the whole unpushed line — general
quality, comment accuracy, test coverage, silent failures — before trusting
it. Two findings arrived from two reviewers independently, which is what put
them first.

**The export tool now settles before it captures.** `export_pdf.py` had
reintroduced the pattern `inspect_layout.py` was rewritten to kill: a bare
300ms sleep, no wait on `document.fonts.ready`, no `pageerror` listener — and
with `font-display: swap` on the embedded face, a capture racing the font is
*guaranteed* to ship fallback metrics under an `ok` line. Worse here than
there: the inspector mis-measures, the exporter mis-delivers. It now waits on
the fonts (5s, explicit FAIL on timeout), fails the file whose own script
threw, refuses a second input whose stem would clobber the first's output,
warns when stale higher-numbered pages from a longer earlier export survive
beside fresh ones, reconciles the PDF's own page count against the section
count, and one bad file no longer aborts the batch (per-file FAIL, browser
closed in `finally`).

**Guards that guarded one of two carriers now guard both.** The 0.1.378
ENTRY_STAMP union fix had reopened its own hole one level up: a stamp file
declared only in ENTRY_STAMP — exactly the scoreboard — could be renamed away
and skipped under a comment crediting the manifest guard, which never covered
it. A missing non-registry stamp file now fails by name, and the negative path
was exercised before shipping. The visual vocabulary's second carrier —
`check_design.py`'s `VISUAL_BLOCKS`, which 0.1.378's own rationale overlooked
while calling the probe's `VIS` "the sole carrier" — is now read by the
probe-vocabulary guard and held set-equal to `VIS`; "a guard that covers one
of two callers is a guard with a blind spot the shape of the other" now has
its caller count right. The genre vocabulary lives once, in
`check_prose.py`'s `GENRES`, imported by `run_conformance.py` and
`export_pdf.py` instead of hand-copied thrice; `export_pdf.py` also gains
`--genre`, so a training deck exported with defaults now ships its primary A4
edition rather than the projection one its help text used to promise and its
default used to violate.

**The proven regressions are pinned.** D10's eyebrow count — which shipped a
zero-count twice, keyed first to `<div>` and then to attribute order — is now
element- and order-agnostic, matches `ic` as a whole class token, and emits a
per-page `D10_detail` that the pass fixture asserts (`contains: p3`); revert
either form of the regression and CI fails. `D16_detail` carries the whole
dict so the pass fixture can assert `"prose_only": []`, closing the
false-positive direction reported verdicts cannot see. `check_fixtures.py`
learns suffixed runs (`prose@training`, `prose@internal`) so M9's training
binding and internal exemption each have an asserted run, and it smoke-tests
the export floor — `--scale 1` must exit 2 naming the floor, checked in CI
with no browser since the check sits ahead of the playwright import.

**Absence is no longer reported as measurement.** `visualPct` is null, not
0%, on a page with no body or a lede taller than it, and the share lines skip
what was never measured; a ground wrapped inside another element — which the
page census counts and the contrast audit cannot isolate — now reports GROUND
UNMEASURED and counts as unmeasured instead of letting the same report say
"continuous on all pages" and "no page draws one" about one document. The
`.grades` and `.field` blocks join the fill-rule exclusion chains before the
chain wins a tenth argument: both declare their own direction and gap, and
only fixture accident had them nested where the chain could not reach them.

**Facts corrected where reviewers caught the prose lying**: six of the eight
svg type classes declare fills, not four of six (comment and changelog both);
the ground generator now draws sixteen genuinely distinct widths, making its
"no two sharing a width" docstring true instead of half-true; the conformance
tuple rejected `training` for two releases, not one; D15's scope sentence
counts four genres; the handling marker's token is `--seal-t` (text-safe on
both canvases), not `--seal`, in both places the prose said otherwise; the
marker sits *inside* `.foot .conf`, not ahead of it; the opener's "nothing
else" scopes to its content area, since its footer legitimately keeps the
inverted marker; the self-contained core prompt finally lists `cover-grid`,
the layout its own frame rule requires; and the fill-chain tally names its
fourth victim (the closenote's 12px) so the "sixth through ninth" arithmetic
can be reconstructed.

## 0.1.378 — what the two audits found in the three releases before it

The owner asked for the 0.1.375–0.1.377 line to be audited before trusting it.
Two independent passes ran: an adversarial audit of the eleven directives
against the shipped state, and a rendered review that read computed styles in a
headless browser. CI was green through both, which is the finding behind every
finding: each defect below sat in the space the green run does not cover. This
release closes them.

**Rendered defects in the promoted vocabulary.**

- The `svg .f-*` paint classes lost to the `svg` type classes by source order —
  every selector is (0,1,1), six of the eight type classes also declare a fill, and
  the explicit win-back list covered `huge`/`mid` only. `class="sm f-acc"`
  rendered ladder-grey; `class="cap-w f-seal"` never turned red; the palette
  guard saw nothing because no literal colour was involved. The paint set now
  sits after the type set, which is the ordering that cannot develop the gap.
  Inherited faithfully from the reference deck, where it is also present.
- The cover-grid and opener children shipped as (0,3,0) rules under the fill
  rule's (0,13,1) `:not()` chain — the typeblock's `gap: 0`, the attrs column's
  3px and the openframe's 26px all computed 14px, the sixth through ninth time
  that chain has quietly won an argument. The five new children join both
  chains, and the chain's comment now states the mirror rule: a new
  `.body > div` child joins it or its declarations are dead on arrival.
- `.sub` was half-shipped: promoted out of the waiver list with a rendering
  scoped to `.cover` alone, so the closing's subtitle fell through to generic
  paragraph styling. Cover and closing are the same kind of page; the rule now
  says so.
- The dark ground ramp was inverted — mid at .24 against strong's .20, a part
  opener denser than the cover — surviving from before the tiers were held to
  a ratio, and left in place when 0.1.375 restated that ratio one palette up.
  Dark mid takes .15 (the same ≈0.76 ratio the light tiers hold); dark strong
  is unchanged.

**Metrics that could not see their own subject.**

- D10 keyed the eyebrow count to `<div class="eyebrow">`, so the fixtures'
  `<p>` eyebrows counted zero and were silently reclassified as figure icons.
  The selector is element-agnostic now and counts 14 where it counted 0.
- The `VIS` list — the sole carrier of the visual-share target — was outside
  `PROBE_CENSUS_LISTS`, so a rename in `tokens/` would have dropped the share
  toward zero with CI green. It joins the guard.
- A deck with no ground read the same as a deck that had been checked
  ("ground: no page carries one", neutral). It now reports GROUND MISSING,
  still never gating: a document outside the brand may be quiet on purpose.
- The 50% visual-share target was ungradeable at A4 — the portrait tokens cap
  a figure at 36svh, and every page of the package's own fixture sat "under
  target" there while healthy. The sheet now reports shares without grading
  them; the target binds in landscape, where it is reachable.
- `check_version_citations` iterated the platform registry's entry files only,
  so ENTRY_STAMP's conformance entry was dead code and the scoreboard's stamp
  sat at 0.1.371 for six releases while the entry's own comment claimed to be
  the check that sees it. The guard now walks the union, and the stamp is
  current.

**The harness catches up with the genre model.** `run_conformance.py` rejected
`training`, the genre 0.1.376 created — the four-genre model had reached the
rules, the checker and all three entry points and stopped at the cross-agent
harness. It accepts it now; T1 also gains the `D15_footer_path` requirement,
which is a gate of equal standing with D12/D14 and was missing from the task's
require list. `export_pdf.py` gains `--genre`: its help text stated the
primary-geometry rule while its default violated it, so a training deck
exported with defaults shipped the projection edition. The raster floor now
binds rasters only — a PDF is vector and has no scale to be under.

**The fixtures exercise what they advertise.** Both now draw the ground —
sixteen deterministic lines, defined once and instantiated per page with
`<use>`, no two sharing a width, amplitude, wavelength or phase, measured
under the 1.40:1 ceiling in all three geometries (1.251 / 1.354 / 1.312 at
the loudest) — plus a `.field` with one mark per datum and its `data-count`,
the graded ladder on one page, the glossary on another, and status chips in
the page-9 table. Until now the suite shipped the brand's signature devices
and rendered neither.

**Prose drift found while auditing, fixed:** the 4K/2K export rule reached
only one of three entry points (now in `AGENTS.md` and the core prompt); the
shield marker was missing from SKILL.md alone of the four restatements; "first
principles" and "the blue team" are now written where their substance already
was; CLAUDE.md's checks list, genre note, scenario list and rubric line;
eval-rubric's M1–M8 heading over a table running to M12, and its D-table's
missing D13 and drawn-share rows; brand.md crediting D13 with enforcement when
only D12/D14/D15 gate; SKILL.md counting four entry points while naming three;
the core prompt counting four block patterns while listing seven.

**Recorded no-changes, so the next audit does not reopen them:** the pass
fixture keeps its 7-page opener runs — the pacing target stays a review
trigger, and the reference deck itself runs longer parts; and `check_prose.py`
still has no `consulting` genre flag — consulting inherits the sales dash ban
by default, which has produced no defect case yet and gets no speculative
flag without one.

## 0.1.377 — the export path ships with its floor in code, and the workflow learns to ask once

The last of three releases carrying the owner's consolidated directive
(2026-08-09). The rules that name tools now have the tools (rule 5), and the
workflow gains the interaction discipline the directive asked for.

**`scripts/export_pdf.py` ships.** §7 has named "PDF export" as a destination
since the geometry axis existed, with no exporter behind it — the exact gap
rule 5 exists to close. The tool renders at the fixed stages and nowhere else:
PDF as one vector page per `.page` (no resolution to pick), and page rasters
at a device-pixel multiplier on the stage — **default 3, which is 4K from the
landscape stage; floor 2 (2K), refused in code** rather than advised in prose,
because a 1x export looks fine on the machine that made it and soft on every
dense display. The scale never touches the CSS stage: every `clamp()` in
`tokens/` is written against the stage, and the HTML edition adapts to the
reader's window and pixel density natively, which is where "auto-adjusting
resolution" honestly lives. Output lands beside the input file, matching the
new output-directory default. Same dependency posture as `inspect_layout.py`:
local, Playwright, py_compile only in CI.

**The workflow learns the interaction rules.** The directive asked for two
things that pull against each other — interrogate the input deeply, and let
one clear prompt produce a finished document — and the arbitration is now
written down: study everything supplied first, work from the reader's side,
and **ask once or not at all** — a missing required input or a genuine
conflict batches every question into one round before generation; anything
less than that becomes a stated assumption in the delivery note. Outputs land
in the input file's directory unless the user names another. Pages compose in
parallel where the platform allows, and a generation expected to pass ten
minutes is announced before it starts. **The red-team pass rides the critic
gate**: the half that built the document argued for it, so the other half
reads it as its most skeptical reader before the self-score — and over-design
is a finding there, not a virtue, which is the directive's own guard against
this skill answering "more expressive" with "more decorated".

All of it re-flowed by hand into `AGENTS.md` and `prompts/lumi-style-core.md`,
where the checklist grows its red-team item and the dash rule names training.

## 0.1.376 — the page anatomy becomes a contract, and training becomes a genre

The second of three releases carrying the owner's consolidated directive
(2026-08-09). 0.1.375 shipped the vocabulary; this one writes the rules that
vocabulary serves, and none of the new numbers gates — each one states its
direction (rule 4) and the two that could have been floors are review triggers
instead, because the withdrawn 82% fill floor is what happens otherwise.

**The deck frame is standardized.** The closing now carries the same single
vector mark as the cover, under the same truth test — a cover and a closing are
the same kind of page, and the closing restates rather than claims anew
(storyline-templates). **Every part boundary gets a lime opener page**, in the
composition the tokens ship; **about five content pages between openers is a
pacing target**, reported by `inspect_layout.py` as the longest run between
openers, never a floor — a target read as a quota would force openers where the
argument has no seam. The opener count line itself stays an observation.

**The eyebrow becomes a contract** (design-rules §3): the page's subject icon,
then `PART <letter> · <this page's own label>`. Deliberately uniform and exempt
from the parallel-structure caution — the eyebrow is apparatus, like the page
number — while titles stay governed by the title contract and M11, which counts
h1/h2 only and never the eyebrow.

**D16, visual presence and share, reported.** The directive's strongest ask —
"more than half of every page should be figure" — is precisely the shape of the
withdrawn fill floor, so it lands as two reported halves instead of one gate:
`check_design.py` D16 lists content pages carrying no visual block at all
(figures, stat bands, display leads and the comparison patterns count; tables
deliberately do not), and `inspect_layout.py` reports each page's rendered
visual area against a 50%-of-content-area **target**. Both are review triggers
for a human; neither can be satisfied by stretching anything, because they
count classified blocks rather than ink. The broken fixture plants a
prose-only page and `check_fixtures.py` asserts the detail names it.

**Training is the fourth genre** (storyline-templates Template 4): for enabling
a team to do something rather than decide something — concept pages, worked
examples, the swap as its workhorse, reference pages a learner returns to.
`check_prose.py --genre training` binds the em-dash rule as sales does, because
training is quoted onward. **And the primary geometry now follows the genre**
(design-rules §7): sales, marketing and consulting design 16:9 first; training
designs A4 portrait first, since it is printed, annotated and bound. The
two-geometry matrix is unchanged — the non-primary geometry is still composed
and verified as the second edition.

**The handling marker becomes a rule** (design-rules §4b): the seal shield
ahead of the terms is the standard rendering on every page. D12 is unchanged —
it gates on the terms, and a page whose terms arrive without the icon has a
style defect, not a compliance one.

**The fixtures now exemplify all of it**: cover and closing on `cover-grid`
with the globe as their shared mark, two lime openers in the shipped
composition, contract-form eyebrows with real Lucide icons via
`embed_icons.sprite()`, the shield in every footer, and a colophon that reads
its version from SKILL.md so it can never drift. The old fixture numbered two
pages `09` and skipped `16`; the rebuilt one numbers 1-18 cleanly.

Stale counts fixed in passing: `check_design.py`'s own docstring said two
metrics gate; eval-rubric's D-table now includes D12 and D16 and its heading no
longer stops at D10; README's rubric line said D1–D6.

## 0.1.375 — the vocabulary the reference deck used now ships, and the dense cover returns

The owner reviewed the recent output trajectory, named the 3.4.0-built deck from
0.1.374's comparison as the reference for how a deliverable should look, and
issued a consolidated directive (2026-08-09). That directive is the documented
case behind this release and the two that follow it: this one ships the
*vocabulary* the reference deck composed with, so that the rules landing next
never mandate a rendering the package does not ship (rule 5).

**Promoted into `tokens/lumi-layouts.css`, generalized and renamed to the
canonical tokens** (the deck's private `--accent`/`--card`/`--seal-text` are
`--acc`/`--card-bg`/`--seal-t` here — a validation artifact is never the
reference for conventions, rule 7; its *design patterns*, owner-designated, are
the facts being imported):

- **`cover-grid`, the sixteenth layout** — the cover/closing grid with its
  `typeblock` / `markcell` / `attrs` / `closenote` cells, plus the `wordmark`,
  `spec`, `sub` and `colophon` furniture. 0.1.370 removed it as a portrait-only
  orphan rather than completing it, explicitly because nobody had asked for a
  sixteenth layout. Somebody has now, so it returns *completed*: base rendering,
  portrait variant, header count, §3 selection row and `check_design.py`'s
  `LAYOUTS` in one change, which is the state `check_layout_parity` forces.
- **The part-opener composition** — `openframe` / `openpart` / `openclaim` /
  `openrun` on the lime field, with the inverted footer. §3's opener bullet now
  describes the three-line composition instead of "one line and nothing else".
- **The geography paint** — `geo-*` classes for the two `assets/vectors/` marks,
  with the cover/closing emphasis weights, plus `geolegend`. The coverage rule
  is unchanged: a region drawn is a region claimed.
- **The figure paint and figure type vocabulary** — the full `f-*`/`s-*` fill
  and stroke set and the `svg` type tiers (`lbl`/`sm`/`cap-w`/`huge`/`mid`),
  replacing the two-class `f-acc`/`f-lime` stub, so no literal colour ever
  reaches a drawing.
- **Block furniture** — the `tag` status chips, the `legend`, the glossary
  `dl.gloss`, and the `grades`/`gr` graded ladder. The ladder was removed in
  0.1.370 as speculative; the owner-named reference uses it on a live page,
  which is the documented case rule 2 requires, so its base rendering ships.
- The `.eyebrow` becomes a flex row and `svg.ic` ships, so the subject icon the
  rules already require has a rendering that needs no per-use nudging.
- **The handling marker** — a seal-red `shield` (the existing reserved binding)
  ahead of `.foot .conf`, at the owner's ask, inverting with the opener field.
  §1's ledger records the extension: the handling line is a standing warning to
  the reader, which is why the warning colour may mark it.

`PROBE_NOT_SHIPPED` shrinks from thirteen waivers to three — `openpart`,
`openclaim`, `openrun`, `grades`, `gr`, `gloss`, `geo-flat`, `sub`, `tag` and
`wordmark` all ship now, and the guard names a satisfied waiver the moment its
class lands, so the deletions ride the same change.

**The ground's strong tier returns to .25 (light, landscape), mid to .19.**
This reverses 0.1.350, which lowered the tier to .20 after the strong ground
broke its 1.40:1 ceiling at A4 on two documents. The owner asked for the dense
cover back, and the reversal was measured before it shipped, on the reference
deck's own ground: at .25 it renders 1.344 against the canvas at 1280x720 —
under the ceiling, because it is drawn with `preserveAspectRatio="xMidYMid
slice"` rather than the `"none"` stretching that caused the 0.1.350 breach —
and 1.413/1.423 at 794x1123, because a cropped ground still concentrates its
densest band on a narrower page. So the sheet takes its own value: portrait
steps the strong tier down to .23, which measures 1.38 on the same deck.
brand.md now names the tier strategy in the owner's terms (dense / medium /
sparse), states that a document defines its ripple drawing once and
instantiates it per page, and requires `slice`. The ceiling itself is
unchanged, measured on the rendered page in both geometries — the tiers stay
ceilings on loudness, and quieter is always allowed.

Ridden along, four drift fixes found while auditing: CLAUDE.md and
design-rules §4b said two `check_design.py` metrics gate when D12/D14/D15 are
three; README still credited "the eight semantic icons" from before the Lucide
library landed; and `prompts/lumi-style-core.md` quoted display-tier clamps
that match no token — its `--fs-lead` carried the stat band's numbers — so the
core prompt now restates the four tiers as `tokens/lumi-theme.css` defines
them.

## 0.1.374 — the step called "Visuals and charts" had stopped mentioning charts

A reader compared a deck built by **3.4.0** against one built by **0.1.373** and
called the newer one less professional. They were right, and the gap is
measurable.

| | 3.4.0 (30pp) | 0.1.373 (14pp) |
|---|---|---|
| drawn figure SVGs | **24** | **1** |
| `.fig` blocks holding a drawing | 14 of 14 | **1 of 5** |
| `<text>` inside SVG | **410** | 8 |
| tables | 4 | **0** |
| figure titles stating a conclusion | 14 of 14 | **1 of 5** |

**The skill had not lost the craft.** §4's five chart rules and its complete
form-selection paragraph were untouched; the icon library, the vectors and the
display face all still shipped. The better deck was made with *fewer* rules. What
had changed is where the path of least resistance led, and three things led it:

**`SKILL.md` step 3 was a gate checklist wearing the title "Visuals and charts".**
552 words in which "figure" or "chart" appeared **once** and checker scripts
appeared four times, running 19 forbidding verbs against 10 making ones. Its only
concrete *compose with* instruction pointed at the four HTML block patterns added
in 0.1.369. An agent following it literally lays out and then verifies, and never
draws. Rewritten as **form → draw → compose**, with form selection first, the
shape vocabulary and figure parity stated inline, and **every gate moved to step
4**, where the other pre-delivery checks already live. It now mentions figures ten
times and checkers none.

**The only worked example in the package drew nothing.** `fixtures/deck-pass` was
**11 of 11 rect-only** — three unlabelled rectangles per page, precisely what D5
exists to flag as weak. Its figure now carries an axis, labelled values, a dashed
bar for the class with no measurement, a conclusion in the caption and a source
line. The broken fixture keeps one rect-only figure so D5 still has a subject.

**Twenty-four consecutive releases of brakes.** `brand.md` set this diagnostic at
0.1.345 — 272 restricting lines to 12 inviting, "nearly five times more braked
than the ratio that already produced bland" — and named inverting the order as
the biggest single quality jump on record. Measured today across `SKILL.md` and
`references/`: **431 brakes to 26 invites**. The ratio improved only because
accelerators were added; the absolute braking load grew **59%**, and `SKILL.md`
itself ran 44 to 3. Step 3 now opens by sending the reader to `brand.md` §3,
which it never reached before.

**D5 gains a reported companion: how many `.fig` blocks hold a drawing.** Nothing
in the package could tell a figure from a layout, which is why a deck of HTML
blocks measured clean on every gate. **Reported, never a floor** — a share here
would be satisfied by drawing badly, which is D7's withdrawn fill floor in a new
costume.

**Two findings from the same week, both the class this release is about.** `.say`
ships as `.lead .say` and nowhere else, so a bare `.say` carried the class the
probe audits and none of the type the token file names; a display claim rendered
at body size on two real deliverables and their pages reported as having no entry
point. It joins the scoped-role audit beside `.k`, `.v`, `.no` and `.yes`. And
**`.field`, the brand's signature device, was missing from `inspect_layout.py`'s
ink census** — measured on a real deliverable, both columns began at the same
pixel while the probe reported 339px of skew, because it could not see the field
and found the caption instead. The fixture has never drawn a `.field`, which is
why nobody had looked.

## 0.1.373 — the language guard existed, and it pointed inward

A Cursor run filed a retrospective on 0.1.371 after shipping three reader-visible
defects while `check_design`, `check_prose --genre sales` and `inspect_layout
--deliverable` all exited 0. It is a good note: it declares itself a retrospective
input rather than a patch, refuses to invent subjective floors, proposes
report-first for its weakest case, and lists what not to do. Two of its three
cases land here as gates; the third lands as a report.

**M12 — an English deliverable must be in English. Gates.** This is the sharp
one, and sharper than the note framed it. `references/writing-rules.md` §0 has set
the output language since 0.1.333, and `check_repo.py:check_english_only` has
enforced the identical red line **on this repository's own prose** for as long —
CJK legal only inside backticks, as quoted data. So the package has a working
language guard, pointed inward, and had never once measured the same rule on a
deliverable. A file named `*.en.html`, carrying `lang="en"`, shipped
`已回收 15/15 题` in a page lede and passed every metric in this package.

The exemption is the repository's own: CJK quoted as **data** — `<code>`, `<pre>`,
backticks, fences — is fine, and nothing else is. No allowlist file, because a
name that must appear in Chinese is quoted, and quoting it is a decision a reader
can see rather than a line in a config nobody reads. The language is read from
`--lang`, then the document's `lang` attribute, then the `*.en.*` filename
convention; when none of the three answers, M12 is `n/a` **and says so** rather
than assuming English.

**D15 — no footer may cite a file path. Gates.** A deliverable poured
`resources/…目录-20260730.zh.html` into the footer of almost every content page,
and D6, D12 and D14 all passed it. **This is the second instance of one defect:**
`.foot .src` was removed from `tokens/` in 0.1.366 after the first deliverable to
meet it printed a build path on every client page. Removing the styling did not
stop the span. Two documents is what this repository promotes to a rule.

Deliberately **not** the genre fork the note proposed. Per-page sourcing is
legitimate for consulting and internal analysis, and an English one-line source
there is apparatus rather than a defect a reader sees; what no genre wants is a
path. Banning the path needs no `--genre` plumbed into `check_design.py` and
catches the thing the reader actually saw. The site D12 *requires* and any URL are
not paths, and the check says so by construction: two segments and a file
extension.

**OPENER INSET — reported, not gated.** An opener set its claim hard against the
page edge while the footer stayed inset, so one page read as two left margins.
`frameSkewPx` compares `.foot` to `.body` and cannot see it — proved, not assumed:
on a fixture with the defect inside the body, the new probe reports 92px while
`frame` reports all seventeen pages sharing one width and centre.

Measured **without a vocabulary**. The note proposed keying on `.openframe`, a
class that ships in no token file — keying a probe on an unshipped name is the
reverse drift `check_probe_vocabulary` exists to stop, and it would see nothing on
a document that names the block anything else. Text ink on an opener may not sit
outside the footer's own edges; `.bleed` is excluded, because running past the
content margin is what that shipped class is for. Report-first is the note's own
recommendation and 0.1.372's rule: one deliverable is one case.

**And the fixture had never rendered a part opener.** `.page.opener` has been
styled since 0.1.345, named in `brand.md`, and counted since 0.1.368 — while no
fixture carried one, so the count was always zero and the new probe would have had
nothing to measure. The same trap as the block patterns in 0.1.369. Adding one
immediately broke two probes that were treating an opener as a content page:

- the **datum** counted it, reporting "content starts at 2 different heights" on a
  deck whose fourteen content pages all start at 202px — a true measurement of the
  wrong set. An opener holds no datum for the reason a cover does not: it is a
  composition, and D8 has exempted it from the support-line rule on those grounds
  since that metric was written;
- the **focal** check excluded its title, reporting a page whose title *is* the
  composition as having no entry point. The exclusion now applies only where the
  frame reserves a title block, which asks the layout rather than naming the three
  page kinds.

Both were found by making the fixture exercise a pattern the package ships.

Two things in the note that do not land: `scripts/verify_gates.py` does not exist —
mutation testing here is done by hand, once per guard, when the guard is added —
and `M5` (zh punctuation) remains in the rubric with no implementation, which is
the same class of gap and is not this release.

## 0.1.372 — a recorded no-change: the column-top skew was the probe, not the page

0.1.371 left one question open. Its passing deck had **three of six multi-column
pages out of line by up to 19px** — the skew a reader once called "the left and
right are not level" — and `COLUMN TOPS` is reported rather than gated. One run
is not a retrospective, so nothing changed. This is the second run, and the
retrospective it makes possible ends in **no change**, which the review protocol
lists as one of its three outcomes and which is recorded here rather than left
as a decision nobody wrote down.

**The columns were never out of line.** Measured directly on the first deck,
every cell box on the three flagged pages starts at exactly the same y —
2408/2408, 3848/3848, 6008/6008. All three findings come from where the **ink**
begins inside those identical boxes:

| page | left cell | right cell | reported |
|---|---|---|---|
| p4 | a filled panel: fill at the box top, first glyph 24px in | SVG drawing starts 6px into its viewBox | 18px |
| p6 | plain `.listhead` text at the box top | SVG drawing starts 17px in | 17px |
| p9 | a bordered `.card` at the box top | SVG drawing starts 6px in | 6px |

Two structural causes, both legitimate: a **painted** block whose visible edge is
the line the eye reads while its first glyph sits inside its own padding, and an
SVG whose drawing begins a few pixels inside its box.

**And it does not recur.** A second deck, same agent, same prompt, same CLI
version: four multi-column pages, **all level**. The check ran and found nothing,
so this is not the absent-subject trap — the skew depends on whether a painted
block or a drawing happens to land at the top of a column, not on whether the
composition is correct.

**So `COLUMN TOPS` stays reported.** Gated, the first deck would have failed on
three findings a reader would call level while the second passed — a gate that
flips on composition rather than on correctness is a gate people learn to route
around. That is the same argument that withdrew D7 in 0.1.340, arriving from the
other side.

**The probe is not changed either, and that is the harder call.** The diagnosis
above suggests a real refinement — when a cell's first element paints a
background or a border, its *edge* is the alignment reference, not its first
glyph. `inspect_layout.py`'s hard-won rule is *ask the ink, never the box*,
written because a grown SVG box reported 0px skew on six visibly crooked pages;
that rule is right for an unpainted box and backwards for a painted one. But this
repository promotes a lesson to a rule **once it has appeared across two
documents**, and this one appeared in one. A probe that has caught 132px of real
skew is not reshaped on a single deck's false positives.

Neither deck is defect-free, and the record should say so: the second carries its
own reported finding — one of its two tables holds prose rather than values.
Neither observation is about the rules.

## 0.1.371 — the first CLI-driven agent through the harness, and the board that erased it

Five releases sharpened the instruments. This one points them at something.

**Claude Code `2.1.226`, headless, through all three tasks.** Run with `claude -p`
in a working directory **outside this repository**, deliberately: run it inside
and the agent reads this repo's own `CLAUDE.md`, which is maintenance
instructions for a rules package and not guidance for producing a deliverable.
The only thing steering it was the skill.

**All three pass.** T1's twelve-page deck clears every design metric including
both gates, every prose metric its genre grades, and **all seven `--deliverable`
findings**. T2 clears the banned-phrase requirement it declares. T3 recalls 5 of
5. That is the first row on the scoreboard earned by a CLI rather than driven by
hand, and it is the first evidence the package's central claim has ever had.

Read as evidence, and the caveats in `run_conformance.py`'s own docstring
govern: one run, one CLI version, one machine, one date. A green row means the
artifact is well-formed and free of the defects we can express as arithmetic. It
does not mean the deck is good — but the contact sheet was read, and the two
pages where the Grok deliverable failed hardest are the two that came back
right: the cover is set in the display register with the wordmark and the
attribute strip, and the closing carries the H1–H6 scoring table, the colophon
and the version stamp.

**Recording it nearly erased the run before it.** `report` built the whole board
from a single `--run` directory, so publishing Claude Code turned Cursor's row
from a measured `fail` into `not installed` — a result that was taken reading as
one that was never taken, in the document whose closing paragraph says absences
are listed rather than omitted. `--run` is now repeatable and merges, later
winning on a collision so a re-run replaces its own cells and nobody else's.
`run` and `score` still act on one directory and say so rather than silently
taking the first.

**One observation that is not a rule change, because one run is not a
retrospective.** The deck passes every gate and still has **three of its six
multi-column pages out of line by up to 19px** — the column-top skew a reader
once described as "the left and right are not level". `COLUMN TOPS` is reported
and not gated, decided that way in 0.1.368, and this run is the first evidence
either way. It cuts both ways: a bordered callout at the top of a column
legitimately starts its ink lower than plain text beside it, which is exactly
what happened on this repository's own fixture in 0.1.369. Whether the gating set
should grow is a judgement, and it needs a second case.

## 0.1.370 — the general form of the last three releases, as two guards

0.1.369 fixed seven font-sizes that existed only inside a media query. This one
asks the question underneath: **why was that state reachable at all?**

**`check_media_only_rules`.** No class may be styled only inside a `@media`
block. A rule that exists in one geometry and nowhere else is a rendering the
package half-ships — the document gets `tokens/`'s value on the sheet and
whatever it invented at 1280 — and it is invisible by construction, because the
consistency audit run at the design geometry finds nothing to compare. One honest
exception, waived with its reason: the landscape/portrait figure pair, where a
figure is drawn twice and each geometry hides one. That is what those two classes
*are*.

It found three things 0.1.369 had left:

- **`.tight` meant nothing at 1280.** The only rule reading the modifier lived in
  the portrait block, so a document adding the class saw no change at the design
  geometry and a quiet one on the sheet. It now tightens spacing in both, and the
  fixture uses it.
- **`.grades` and `.gr .gc` are removed rather than completed.** Neither had a
  base rendering, `references/` never named either, and no fixture drew one —
  three orphan declarations styling a block this package does not ship.
  Inventing a graded-criterion design to justify them is the speculative
  rule-making CLAUDE.md rule 2 forbids.
- **`.body.cover-grid` is removed.** A *sixteenth* layout, declared only in
  portrait, missing from the token file's own "fifteen page layouts" header,
  missing from §3's selection table, and missing from `check_design.py`'s
  `LAYOUTS` — so D9 read a page using it as using no shipped layout at all.

**`check_layout_parity`** keeps that last one from recurring: the layouts
`tokens/` defines and the layouts `check_design.py` grades are one list, checked
in both directions.

**And the vocabulary guard was reading one caller of two.** `check_prose.py` keys
on class names too — five `(wrapper, item)` pairs it counts as enumerations for
M10 — and 0.1.368's guard never looked at it. Widened, it immediately named
`.grades`, `.gr` and `.gloss` as asserted-and-unshipped. All three are **census**
assertions in the 0.1.368 sense: they ask to be counted, not to be rendered, so
they are waived with a reason rather than given a design. *A guard that covers
one of two callers has a blind spot the shape of the other.*

**That widening also found a live bug.** The tuple matched every item as
`class="…item…"`, and a glossary's items are `<dt>` **elements** — so the
`("gloss", "dt")` pair counted zero on every definition list ever written, and
M10 silently sampled one enumeration shape fewer than it claimed. The pair now
says which kind each item is; measured on a three-term glossary, 0 became 3.

## 0.1.369 — the portrait block stated the rule and broke it in the next twenty lines

`tokens/lumi-layouts.css` carries this, above its portrait overrides:

> What tightens here is SPACING, never the type of a named role… a page that no
> longer fits gets its CONTENT trimmed, never its type nudged.

**Seven rules immediately below it set a font-size.** `.notes li` at 12px, a notes
table at 11.5px, `.key` at 12px, `.no`/`.yes` at 12px and 11.5px, `.ledname` at
18px, `.card dd` at 12.5px — and **not one of those classes had a base rendering
anywhere in `tokens/`**. The portrait value was therefore the only value the
package shipped: every one of them rendered one way at A4 and whatever a document
invented at 1280. One role, two renderings, from the file that carries the rule
against them. Eighteen releases, and the same trap that caught `.gd` in 0.1.350.

0.1.368's probe-vocabulary guard is what surfaced it, by asking a question nobody
had asked: what does `tokens/` actually *ship*? Twelve waived class names turned
out to be four repeating block patterns that this package has audited for four
releases and never rendered.

**All four now ship a base rendering**, and every size is an existing tier chosen
by what the thing is rather than invented — block body text is `--fs-fig-title`,
the size `.gd` has occupied since 0.1.350 and the same voice; a card's name is
`--fs-support`; a vow's number is `--fs-fine`. No new token, because a new tier is
a design decision and nothing asked for one.

- **tier-1 callout** — `.key`, and `.red` for a red line. `check_design.py` has
  named both as `TIER1_CLASSES` since D3 was written while `tokens/` shipped
  neither.
- **card** — `.card`, `.ledname`, `.verdict`, and the `dl`/`dt`/`dd` inside it.
- **swap** — `.swap` with `.no` and `.yes`, scoped for the reason `.band .k` is:
  those are the two most collidable class names in the vocabulary. Scoping them
  means auditing outside the scope, so they join the unscoped-role audit.
- **vow** — `.vow` with `.vn`, `.vt`, `.vw`.

**`.duo` too**, found the same way from the other end: its base grid existed only
inside the media query that collapses it, so at the design geometry it was a plain
block and its children stacked — 12px past the footer rule on the first fixture
page to use one. *A container that exists only in the geometry that undoes it is
the same defect as a font-size that exists only there.*

Every text role here carries `margin: 0`, for 0.1.367's reason: a role is one
rendering **including its box**. Measured on the vow grid before the fix — 30px
between a vow's title and its body where the block asks for 6.

**The fixture used none of these blocks**, which is why the defect could sit
still for eighteen releases: nothing in this repository ever rendered one. Four
pages now do — a `sidebar-notes` page with the callout and two swaps, a `stack`
page of cards, a `stack` page of vows, and a red-line callout on a fourth. It
also exercises `.lead.row`, which nothing had rendered either.

**Both fixture pages overran, and `--deliverable` said so before anything was
committed** — 44px past the footer rule at 1280 and 135px at A4. The rule for a
page that does not fit is that its *content* is trimmed, so the content was
trimmed: a page about four commitments does not also carry a bullet list and a
display number. That is the gate shipped in 0.1.368 doing its job on this
repository's own work, one release later.

**And moving a fixture page broke a planted defect.** Page 5 became a cards page
with no `.gd`, so the D4 literal-colour plant vanished with it and D4 came back
`ok` on the fixture whose job is to make it fire. `check_fixtures.py` caught it.
*A defect that stops being planted is indistinguishable from a check that stopped
working.*

Still not shipped, and recorded rather than invented: `.grades`/`.gr`/`.gc` and
`.body.cover-grid`, which have the same portrait-only shape but set no type — and
`cover-grid` is a sixteenth layout absent from `check_design.py`'s `LAYOUTS`.

## 0.1.368 — a gate nothing invokes is not a gate

Three releases of finding defects the instruments could not see, and this one
turns the instruments on. It closes the vocabulary class and makes the one tool
that renders a page able to fail.

**`check_probe_vocabulary` — the reverse-drift rule, mechanized.** A probe that
keys on a class name is asserting a vocabulary, and this repository has shipped
that defect three times: 0.1.349 audited ten roles against six names that
appeared nowhere in `tokens/`; 0.1.361 shipped `.cap .srcline` and not
`.foot .src`, so a comparison between them could never run; 0.1.366 found
`.cover h1` and `.closing h2` audited as two of three title registers and shipped
by nothing. The guard reads `inspect_layout.py` with `ast.parse` — never by
importing it — and separates two kinds of selector:

- **contract** (`ROLES`, `SCOPED`) claims a role renders exactly one way. A claim
  about rendering must have a rendering behind it, so these **may not be waived**.
  All of them resolve today, which is what 0.1.366 and 0.1.367 bought.
- **census** (`INK`, `TSEL`, `DSEL`, `CENTER`) asks only to be counted and
  over-reaches on purpose. Twenty-two of these ship nowhere, each now listed in
  `PROBE_NOT_SHIPPED` with a written reason.

**Shipped means a BASE rendering.** Seven of those twenty-two — `.key`, `.red`'s
partner, `.card`, `.swap`, `.vow`, `.no`, `.yes`, `.ledname` — are styled by
`tokens/lumi-layouts.css` **only inside the portrait media query**, which tightens
a font-size the file never declares at 1280. The stylesheet overrides a rendering
it does not ship. Accepting a media-query appearance as "shipped" would have let
the guard report the vocabulary complete on the strength of a portrait override,
so it does not. Those base renderings are a design decision and are not invented
here (CLAUDE.md rule 2); the guard records the debt where the next reader will
find it.

**`inspect_layout.py --deliverable`.** Its design judgements still gate nothing —
that is `SKILL.md` rule 4 and D7's withdrawal, and it stands. What gates is the
subset that is **decidable rather than aesthetic**: collision, content spill,
page height, hidden content, an overspent title reserve, a role split, a lost
datum. Focal weight, column balance, caption distance, centerpiece scale, empty
band and the new part-opener count stay reported, because the fix for each is a
design decision and a number satisfiable without improving the page ends the
looking. Without the flag, behaviour is unchanged. Every predicate is defined
once and read twice — by the report and by the gate — because a gate that
disagrees with the text printed above it is worse than no gate.

**Part openers are reported, never floored.** `.page.opener` has been styled in
`lumi-layouts.css` and named in `brand.md` while nothing required, reported or
checked it, so a deck with six read identically to a deck with none. How many
part divisions a document wants belongs to its storyline; a minimum here would
grow openers to satisfy the number.

**The harness had never run the instrument that renders the page.**
`run_conformance.py` scored prose and design only. `layout` joins `SCRIPTS`, runs
with `--deliverable`, and `T1-deck` gains it — along with `D14_placeholders`,
`collision` and `content_hidden` in its `require` block. A task naming a scoring
kind nothing can run now fails validation instead of raising `KeyError` halfway
through a scoreboard and discarding every row already graded.

**And `--json` was the mode whose exit code lied.** All three report functions
*return* what they could not measure, and `main()` called them only when not
emitting JSON — so the machine-readable mode, the one a harness consumes, counted
zero unmeasured checks forever. Measured: a deck with three `NOT MEASURED` lines
exited **0** under `--json` and **1** without it. The functions now always run
and their output is swallowed instead. "A check that did not run is not a check
that passed" cannot be true only in the mode a person is watching.

**Re-scored, and the transition is the evidence.** The recorded Cursor run moves
from `pass` to `fail (design exited 1, layout exited 1, D14_placeholders=FAIL,
collision=FAIL)`. Five of the seven layout findings fire on it — collision,
content spill, an overspent reserve, a role split and a lost datum — on an
artifact this repository had already published as conformant.

**One near-miss worth recording, because it nearly shipped a gate people would
learn to ignore.** The hidden-content check first flagged **26 of 30 pages** of a
real deliverable, every one of them the eyebrow's `<svg class="ic">`: SVG carries
`overflow: hidden` from the UA stylesheet, and an icon is not text however close
to the title it sits. Scoping it to text-bearing, non-SVG boxes then swung too
far the other way — asking for an element's *own* text nodes excused the `.lede`
container, which is exactly where the clamp that deleted three title lines sat.
It asks for text anywhere beneath a non-SVG box. **A gating finding has to be
falsified in both directions**: once that it fires on the defect, and once that
it stays quiet on a clean document. The first version passed the first test.

## 0.1.367 — the overlap was a reserve overspent, and the fix hid the text

The overlapping text on the Grok 4.5 deliverable turned out to be one page, one
rule, and one wrong answer to it. Its closing page was authored as a **body**
page, so it inherited the title reserve meant for content pages; its title ran to
four lines in a two-line reserve; and `lumi-layouts.css` states the rule in the
direction that matters — *a title needing three lines does not get a taller
reserve, it gets shorter text.* The agent added `-webkit-line-clamp: 2;
overflow: hidden`.

**Three of four title lines and the tail of a support sentence never render.**
Deleted content on a client page, and **every geometric probe in this package
passed it**: clamped text produces no spill, no collision and no page overflow.
The rule was right and the agent broke it — but the skill gave it no way to find
out.

Two signals, both measured on the rendered page and neither keyed to a class
name:

- **the reserve is overspent** — what a `.lede`'s children need against what the
  block reserves;
- **content is being hidden** — a clamp or a hidden overflow inside one, which is
  never legitimate there.

A deep diagnosis had proposed comparing `scrollHeight` to `clientHeight` element
by element. **Verified before acting, and it is wrong**: `h2.t` is a 35px box
holding 42px of ink, because `--fs-title` resolves to 34.56px against a
line-height of 1.02. That is the tight leading this design uses on purpose, and
such a check fires on every correctly-set title in the system.

**Then the probe found the defect in the package that ships it.** Run on this
repository's own fixture it reported ten of fourteen title blocks over their
reserve, by 31px each. `.body .lede` declares `gap: 10px` and `justify-content:
flex-start` — the `+ 20px` in the reserve formula is two of those gaps — and
neither had applied for four releases, because `.body > div:not(…)` reaches
(0,7,1) against this rule's (0,2,0). The named roles also carried the UA's `<p>`
margins: `<p class="eyebrow">` and `<p class="sup">` added 58px the formula never
knew about, a third of the block. **A role is one rendering including its box.**
Both fixed; `.eyebrow`, `.sup`, `.listhead` and `.gd` now ship `margin: 0`, and
the column-top skew on the fixture went from 12px to zero as a side effect.

Adding `:not(.lede)` to that fill rule then broke the multi-column rule that
depends on carrying one more class than it — column skew jumped from 12px to
107px inside one edit, and the probe caught that too. **Fifth time this chain has
quietly decided an argument.** Both chains now carry the exclusion.

**`--accent` was referenced by `tokens/lumi-layouts.css` and defined in neither
token file.** The semantic accent has been `--acc` since the palette existed, so
the footer origin line and the emphasis inside a display number inherited
whatever colour sat above them. Same shape as the `var(--display, var(--sans))`
defect fixed in 0.1.352, and a name read out of a deliverable's private CSS.
`check_repo.py` gains **`check_token_references`**: every `var()` in `tokens/`
must resolve, recursively through its fallbacks, or be waived with a reason.
That is half of what 0.1.366 promised for this release — the custom-property
half. The class-selector half, `check_probe_vocabulary`, moves to 0.1.368
because the overlap diagnosis took priority.

**A scoped role audit hides its own subject.** `.band .k` and `.band .v` report
"one rendering" on a document whose `.k` and `.v` render five ways each, every
one of them outside a band, where `tokens/` says nothing and the author
necessarily invented the rendering. The scoping is not the error — a band value
and a lead value are two roles on purpose — reporting only the scoped uses is.
Uses outside the shipped scope are now counted and named.

**D14: no slot the author left for themselves may reach the reader.** The
deliverable shipped four `[TO FILL]` markers on its closing page, beside its own
callout saying they must not ship. It **gates**, for D12's reason: it is not a
judgement about whether a page is well made, it asks whether the document is
finished, and that is decidable. Nothing else could see one — a placeholder is
not a banned phrase, not a colour, and occupies exactly as much room as the text
that should have replaced it. Bracketed ellipsis is deliberately not a marker.

**And `check_design.py`'s own summary was a lie by construction.** It counted
rows whose verdict was `"note"` — a value `grade()` has never produced — so the
counter was always zero and the last line of every run read **"nothing flagged"**,
including under a report carrying two FAIL rows. That is the exact sentence
quoted at the top of the 0.1.366 entry as evidence that every instrument in this
repository passed a broken document. The instrument was not wrong about the
metrics; it was wrong about itself. A summary is a claim about what is above it.

The fixtures carry both halves: the broken deck now plants a `[TO FILL]`, and the
footer drops the `.src` span that 0.1.366 removed from the token file and left
behind in the reference implementation of its own rules.

**Verified on the real deliverable**, at each stage: `check_design.py` moves from
`nothing flagged`, exit 0, to `D14_placeholders FAIL` on three named slots, exit
1. Both fixtures were re-run at all three geometries with no new `NOT MEASURED`
and no verdict change except the intended ones — the column-top skew closing to
zero and the collision on the broken deck's overlong support line disappearing,
both consequences of the margins the roles now own.

## 0.1.366 — the fixture was never loading the stylesheet it was testing

A deliverable built in Cursor with Grok 4.5 came back with its cover and closing
set in the wrong face, an internal build path printed in every page footer, and
page numbers wrapped onto their own line. **`check_design.py` reported "nothing
flagged" and `check_prose.py` reported "all metrics pass", both exit 0.**
`inspect_layout.py` found six real problems and exited 0 too, because design
judgements gate nothing — and `run_conformance.py` never runs it at all. Every
instrument in this repository said the document was fine.

**The fixture inlined the `:root` block and reimplemented everything else.** Its
own `.body.split`, `.lede`, `.eyebrow`, `.sup`, `.listhead`, `.gd`, `.band`,
`.lead`, `.cap .n`, `.foot` — every one of which ships in `lumi-layouts.css`. So
the shipped layout stylesheet **was never loaded by anything in this
repository**, and its gaps were invisible by construction. A fixture that
reimplements what it is testing is testing itself. It now inlines
`tokens/lumi-layouts.css` in full and keeps only what a document legitimately
decides for itself.

Three gaps that had been hiding behind it:

**`.foot` never got `display: flex`.** `.foot .site` has carried
`margin-right: auto` since the footer existed — a property that does nothing
outside a flex container. The rule was inert, the spans ran inline, and the page
number wrapped. Shipped now.

**`.cover h1` and `.closing h2` appeared zero times in `tokens/`**, while the
consistency probe has audited them as two of its three title registers since
0.1.352. A deliverable wrote its own, without a `font-family`. The audit called it
clean, because **one rendering is what it checks and one rendering is what it
got** — consistency is not correctness. Both registers ship now.

**`.foot .src` is removed.** It shipped in 0.1.361 with styling and no rule about
what it was for, and the first deliverable to meet it filled every client page
with a source path and three processing dates. `design-rules.md` already says
sales and marketing state provenance once for the document, in the closing
colophon; a per-page source slot contradicted the rule and existed only because a
probe compared against it. The source-echo audit now compares a figure's source
line against the document colophon. **Shipping an asset with no rule is the mirror
of CLAUDE.md rule 5, and costs the same.**

This is the third instance of the same class — 0.1.349 audited ten roles against
six unshipped names, 0.1.361 shipped one half of a compared pair — and the pattern
is now explicit: **the skill has been auditing a larger vocabulary than it ships.**
0.1.367 mechanizes the check that stops a fourth.

## 0.1.365 — the task said what it was and nothing carried the word to the checker

Cursor's twelve-page deck failed `M9_dashes` on two em-dashes in a term-and-
definition list. `references/writing-rules.md` 8 bans the dash in **sales and
marketing** deliverables and says in the same breath that it *"does not bind
internal analysis documents"*. T1 has called itself an internal analysis deck in
its title since the day it was added.

**The harness never passed the genre.** `check_prose.py` has taken `--genre` since
it was written; `score_checks` built its argv without it, so every deliverable
this scoreboard has ever graded was graded as sales material whatever it was. A
task could declare its nature in a title and in no way that reached the checker.

Genre is a field now, `score_checks` passes it, `load_tasks` rejects a genre
`check_prose.py` does not accept, and it is part of the run fingerprint — it
changes the verdict, so a run scored under a different genre is stale rather than
comparable. Cursor's deck, graded as what the task says it is: **three of three
pass**, with M11 at 58.3 against a 60 ceiling — the first time that metric has
been exercised by any agent, because the six-page version of this task could never
reach its eight-title floor.

This is the third defect the Cursor run has found, and none of the three was
Cursor's: an em-dash placeholder in a table cell, a task shorter than the floor of
the metric scoring it, and now a genre that existed only in prose. **We had never
run these checkers against output we did not write**, and every fixture in the
repository was authored by the hand that authored the checks. Each of these was
invisible to a suite that only ever read its own homework.

## 0.1.364 — a result is a result of a question, and the question had changed

0.1.363 recorded Cursor at three of three, and in the same release changed T1 from
six pages to twelve. The scoreboard went on showing the six-page `pass` with
nothing to indicate it was answering a prompt the repository no longer contained
— and the change was not cosmetic, since twelve pages move M11 from ungraded to
graded. The recorded verdict was for a strictly easier task than the one on disk.

`score` now fingerprints **the prompt the agent was actually shown**, read from
the `PROMPT.txt` in the run directory, and `report` marks a cell
`stale: task changed` when that fingerprint no longer matches the task. A stale
cell is neither a pass nor a failure; it is a result that has to be re-earned.

Fingerprinting the *task* rather than the prompt was the obvious first cut and it
was wrong: scoring re-reads the artifact from disk, so hashing the current task
stamped a fresh fingerprint onto an old answer and called it current — the six-page
deck went on reporting `pass` against the twelve-page task. The hash has to come
from the question that was asked, not from the question being asked now.

Only fields that can change a verdict are hashed: `prompt`, `deliverable`,
`score`, `require`, `answers`, `input`. `title` and `note` are documentation, and
rewording them must not invalidate a run — verified in all three directions.

Cursor's T2 and T3 still read `pass`; those tasks are unchanged and their results
stand. T1 reads `stale`, which is the honest state until it is re-run.

## 0.1.363 — the first agent outside Claude Code, and the checker was wrong

Cursor was installed from the registry path, driven by hand through all three
conformance tasks, and scored. **Three of three pass** — the first real reading
this scoreboard has ever carried, and the first evidence that the claim behind
this whole release line survives contact with a different model.

| task | result |
|---|---|
| red-line recall | **5/5** — seal red and its hex, "AI never signs", "source or derivation", "exactly one focal element" |
| de-AI rewrite | **pass** — 14 seeded banned phrases to 0 |
| twelve-page deck | **pass** — every design metric clean, including D12 |

**The one failure in the first run was ours.** T1 came back `M9_dashes = 1`, and
the dash was `<td>&#8212;</td>` — an empty-cell placeholder, the standard
typographic convention for "no value". M9 exists to catch em-dashes in *prose*, an
AI-flavor tell; it counted a table cell and failed a deliverable that had no such
dash in a sentence anywhere. The numeric-range exemption already in the checker
shows the mechanism was right and the case was simply missed. Cell placeholders,
in both literal and entity form, are now exempt.

This is worth recording as a class: **we had never run these checkers against
output we did not write.** Every fixture in this repository was authored by the
same hand that authored the checks, so a convention we happened not to use was a
convention the suite could not see. The fixtures now carry both cases — a
placeholder that must not fire, and a prose em-dash that must — and removing the
exemption fails the suite.

**A task shorter than the checker's floor measures nothing.** T1 asked for six
pages while M11 needs eight titles to grade, so it reported `n/a` every run and
the task could never exercise the metric it was scoring against. It asks for
twelve pages now.

**`run --agent <id>`** prepares a task directory for a platform that answers no
probe. Cursor is an IDE, Antigravity is an IDE, Kimi and DeepSeek are API models —
four of twelve platforms can never be detected, and the harness only served the
ones that could, so the most common case required building the directory by hand.

**`report --run` now reads `scores.json`** instead of rendering "not run" into
every cell regardless. An agent driven by hand shows its real verdicts and its CLI
column reads `driven by hand`, which is what it is.

## 0.1.362 — the fixes had been re-enacting the defect they closed

A second review of the fix releases returned a verdict worth recording plainly:
**every one of the four contained at least one fix that re-enacted the defect
class it was written to close.** Five rounds now. That is not bad luck.

**The raise added to catch an empty description could not catch an empty
description.** `skill_field` returned early on an inline scalar, so
`description: ""` — the precise case the guard's own comment cites — never
reached the emptiness test, and the manifests shipped an empty field with CI
fully green. The test now runs on both paths.

**The scoreboard read one flag and ignored the other.** 0.1.358 fixed `score`
passing a crashed checker by reading the `unparseable` flag it had been writing
and never reading. It went on writing the checker's **exit code** into every
record and never reading that: `require` names two metrics of eighteen, so an
artifact failing sixteen others scored `pass`. Same defect, same release, one
field over. A parseable report that graded nothing now counts as unparseable too
— a `deliverable` glob matching a directory produced exactly that and read as a
pass.

**The fixture was still shaped around the bug it was supposed to test.** 0.1.359
fixed the footer parser and left the fixture using spans to avoid the old one, so
the buggy regex still passed the suite — the parser fix was never tested by
anything. The fixture footer now nests a `<div>` deliberately, and reinstating the
old regex fails the suite, which is the only evidence that the fix is real.

**The stale-promise guard, having stopped over-matching, stopped matching at
all.** Removing the bare `from` in 0.1.361 cured the false positives on
retrospective citation and blinded it to its founding case — the registry's own
*"from 0.1.354 … will generate"*. An inventory of verb phrases was the wrong
shape in both directions; it now matches any shipped version named in a
future-tense sentence, and reads the generated entry points and manifests it
previously could not see.

**Recall scoring, fixed for one hole, opened another.** Matching by ordinal
position marked a correct answer sheet 0/5 when the agent echoed the prompt's own
five numbered questions above its answers — failing a recall task for a formatting
reason unrelated to recall. It keys on the literal number now.

Also closed: a run directory with nothing in it reported zero rows and exit 0;
unknown task directories were dropped silently, so renaming a task erased every
prior result for it; a task with an empty `score` list passed anything, and four
other malformed shapes crashed mid-scoreboard and discarded every row already
scored; a guard returning `None` read as a guard that found nothing; a `probe` of
the wrong type published an installed agent as absent.

*The pattern is the finding.* Five rounds of hand-written guards, each closing a
defect and carrying a new instance of it. What has actually worked, every time, is
mutation testing — reintroducing the defect and checking the guard notices. That
belongs in the suite rather than in a reviewer's hands, and it is the next thing
this repository needs.

## 0.1.361 — half a vocabulary makes a check look wired up

A review of the four fix releases found the fixes had reproduced the defect class
they were fixing, for the third round running.

**`.foot .src` was never shipped, so an audit reported success on every document
that will ever be measured.** 0.1.359 added `.cap .srcline` to `tokens/` to close
the assert-before-you-ship gap, and shipped only half the pair: the source-echo
audit compares a figure's source line against the footer's, and `.src` existed
nowhere — not in `tokens/`, not in `references/`, not in either fixture. So
`footSrc` was structurally always null, the comparison never ran, and the probe
printed *"no page states the same source twice"* unconditionally. **That is worse
than shipping neither**, because the check now looked wired up. `.foot .src`
ships, the fixture emits it, and the audit reports `NOT MEASURED` when there is
no pair to compare rather than reporting success.

**A task file documented behaviour its code did not have.** T3's new `scoring`
field claimed word-boundary regexes "matched per numbered answer line". The code
matched the whole document, so `\bone\b` for question five was satisfied by
question three's own "no one" — and a one-line reply answering nothing scored
**5 of 5**. Answer *i* is now matched against line *i*. The same junk reply now
scores 0 of 5. Writing the claim into the file before the code was worse than the
honest substrings it replaced.

**The rewritten maintenance rule 3 re-enumerated, and was wrong the day it
shipped.** It replaced "five places… and they are the only ones" — false for six
releases — with a tier naming six generated files when there were eight. That
tier now says "everything `build_entrypoints.py` writes" and deliberately lists
nothing: `--check` is the forcing function and it needs no inventory. Rule 3 also
filed `conformance/CONFORMANCE.md` under "not a stamp" while line 1 of that file
is a first-class skill stamp, hand-bumped in the same release. It is in
`ENTRY_STAMP` now, so a stale one fails instead of staying legal forever.

**`check_stale_promises` was one sentence from a false failure.** Its pattern
included a bare `from`, which matches "carried over from 0.1.352", "survived from
0.1.340", "renumbered from 0.1.328" — retrospective version citation being this
repository's entire documentation voice. It would have failed CI while asserting
the opposite of what the sentence said. Every alternative is future-tense now.

**0.1.358 silently mangled a token authority.** A `json.dump` round-trip with
`ensure_ascii=True` and no trailing newline turned seven em-dashes in
`tokens/design-tokens.json` into escapes and dropped the final byte. Nothing in
that release mentioned touching the file and no guard catches encoding — palette
parity compares values. Restored.

Also: `run` announced a directory it had not created when few agents were
detected, which is the case the scoreboard itself documents; `expected.json`
overstated what its new coverage buys, since four D-metrics are reported rather
than graded and both D3 tiers pass vacuously on fixtures carrying no tier-1
callout; `CLAUDE.md` claimed in one paragraph that CI cannot run the deliverable
checkers and in another that it runs them on the fixtures every push — CI does run
two of the three; and a duplicated draft comment in `inspect_layout.py` is gone.

*Outstanding and named:* the reference fixture reports `COLUMN WEIGHT` on 12 of 14
pages at A4, because its two cells carry very different ink. It is a reported
diagnostic that gates nothing, and it is a design job on the fixture.

## 0.1.360 — the documentation catches up with six releases

Nothing new is built here. Five releases of machinery landed while the files that
describe the repository went on describing the repository as it was at 0.1.351,
and `CLAUDE.md` names that exact hazard on its own first page.

**Maintenance rule 3 had become false, in the document that binds.** It said the
version lives in "**five places** … and they are the only ones a version string
lives." It stopped being true at 0.1.352 and stayed for six releases. The version
now lives in three tiers and the rule says so: hand-stamped-and-checked (SKILL.md,
CHANGELOG, three token files, `AGENTS.md`, the core prompt), generated (the plugin
manifests, the `.well-known` index and the three pointer files, which
`build_entrypoints.py --check` keeps current), and not-a-stamp (historical notes
in the theme; third-party CLI versions on the scoreboard). The forcing function is
named for each: adding a token file means adding it to the tuple in
`check_versions`, adding an entry point means adding it to `ENTRY_STAMP`, and a
stamp with no declared position fails rather than being skipped.

**The Checks block listed one of the four new scripts** and the CI-guard summary
listed none of the three new guards, so three of the five commands a reviewer must
run to reproduce a release were undocumented in the file that documents the
commands. `README.md`'s file map was unchanged from 0.1.351 and had no entry for
`fixtures/` or `conformance/` at all, though both are tracked top-level
directories the README already links into.

**One sentence in `CLAUDE.md` was unparseable** — two edits collided in the clause
that states where the `references/`-wins precedence rule is documented.

**The registry made two claims it could not support.** Its Hermes record cited
OpenClaw's repository as Hermes documentation — a different project — while the
record's own waiver said no documentation could be cited; and it declared a CLI
probe that has never been run, which satisfied the guard built to force unverified
claims into the open, because that guard only asked whether the field was null.
Both are now null with written waivers. The registry also carried a hand-written
version stamp, unguarded and four releases stale; it is gone, because the registry
is not a copy of the rules and has nothing to drift from.

**The third-party version exemption was file-wide.** It was justified entirely on
the agent CLI builds the scoreboard records, but exempted the whole file,
including the skill's own stamp on its first line — so the one file that makes
versioned claims about this repository was the one file where those claims went
unchecked. It is now scoped to the table rows that carry them. Falsified: a bogus
`lumi-style 0.9.999` in the scoreboard's prose now fails.

## 0.1.359 — the fixture suite starts proving what it claimed

0.1.355 shipped two fixtures to test the check scripts, and the review found the
suite could not do the job it was built for.

**Ten of thirteen design metrics were asserted on neither fixture.** `D1_contrast`,
`D6_footer`, `D8_support_line`, `D9_layout_spread`, `D10_label_icons`,
`D13_lime_as_text` and four more returned `ok` on both documents and were checked
against nothing, so any of them rewritten to `return "ok"` unconditionally would
have passed the suite. That is the 0.1.350 defect one level up: a regression test
built to prove the checkers fire, unable to notice a checker that stopped firing.
`expected.json` now asserts every metric each checker emits, on both fixtures.

**The one gating design check had a real parsing bug, and the fixture was written
around it.** `d12_commercial_footer` captured the footer non-greedily to the first
`</div>`, so a deliverable wrapping its handling terms in a nested `<div>` failed
the only check that blocks a ship — for a reason having nothing to do with the
terms being present. `build_fixtures.py` carried a comment explaining precisely
this and used spans to avoid it, which guaranteed the regression suite could never
surface it. That is the letter of `fixtures/README.md`'s own rule, written in the
same release: **never edit a fixture to make a check pass.** The parser now
balances the element's own tags, and D6 and the colophon check, which carried the
identical shape, use it too.

**`.srcline` and `.f-acc` were asserted before they were shipped.** The
component-colour audit keys on `.f-acc` and both fixtures emit both classes, while
neither existed in `tokens/`. This is the reverse-drift CLAUDE.md names and the
defect 0.1.349 was penalised for, at smaller scale but load-bearing rather than
incidental: they were gated by `--check` in CI. Both now ship.

**Two recorded numbers were wrong, and one task was unfailable.** T2 claimed six
banned phrases in its seeded passage; `check_prose.py` measures fourteen. T3's
recall key used bare substrings, so `"not"` matched *note*, *cannot* and
*nothing*, `"1"` was guaranteed by the prompt's own instruction to number the
answers, and `"red"` matched *red line* and *required* — three of five questions
could not be failed. Measured after the fix: an answer sheet of "I do not know /
Not sure / Cannot say / No idea / Nothing" scores **0 of 5**, where it previously
scored 3. A recall task an agent passes without loading anything measures nothing.

Also: `glob` is now `sorted`, so an agent that leaves a second Markdown file
alongside its answer cannot make the scored artifact depend on filesystem order.

*Not fixed here, and worth naming rather than burying:* `deck-pass.en.html` still
uses one layout on all fourteen body pages and carries none of the eight semantic
icons — the pathology `D9` and `D10` exist to report. Both metrics are now
asserted, so the decay is at least visible; making the reference deliverable
actually model layout variety is a design job, not a test job, and it is
outstanding.

## 0.1.358 — absence stops meaning assent

A review of the five preceding releases mutation-tested every new guard and found
the same defect in all four new scripts and three of the guards: **the code read
absence as agreement.** A missing frontmatter field, an empty section, an omitted
flag, an unemitted verdict, an unparseable report, an empty spec — each was
treated as "fine" rather than "unknown". That is the defect 0.1.350 removed from
`inspect_layout.py`, reproduced inside the machinery built to prevent it.

**`--check` certified garbage.** `skill_field()` returned `""` for a field it
could not find, so renaming `description:` in `SKILL.md` rendered three manifests
with an empty description and `build_entrypoints.py --check` called them current —
with the same sentence it uses for correct output. The structural point is worth
keeping: `--check` compares the tree against what the generator produces *now*, so
it can catch a stale tree and can never catch a generator whose extraction failed.
Extraction now raises. So does `red_lines()` on an empty section, which had let
all three pointer files ship a heading promising six non-negotiable rules with
nothing beneath it, every guard green.

**The conformance scoreboard passed a crashed checker.** `require` was checked
per-checker, which forced an `is not None` clause to skip the other checker's
metrics — and that clause also swallowed a required metric that reported nothing
at all. A document using none of LUMI's tokens returns `UNMEASURABLE`, so an agent
emitting exactly that scored green. `require` is now checked once against the
union of every checker's verdicts, a metric that never reported is a failure, and
the `unparseable` flag that was written into the record and never read is now a
failure too. An empty JSON list also crashed the scorer mid-scoreboard.

**Deleting one optional field stripped a published warning.** `path_verified` was
only checked for an explicit `false`, so removing it turned an install path the
repository admits is a guess into an apparently-verified instruction, in the
generated note. It now requires an explicit `true`. `docs: ""` and `probe: []`
satisfied `is None` and no longer do — `probe: []` was worse than cosmetic,
because `detect()` read it as no probe while the manifest guard called the record
complete, so the two files disagreed about what "has a probe" means.

**A ratchet that was never a ratchet.** A comment claimed that a note promising
work "in 0.1.354" became a CI failure once 0.1.354 shipped. It did not: the
citation guard fails only when *no* heading defines a version, so shipping made
the promise more legal, and it globbed `*.md`, so the registry's own two stale
promises were never read at all. `check_stale_promises` is the check that comment
described, and it scans the registry JSON as well. The registry's promises are
gone.

Smaller, same class: a guard that raised took every guard after it with it and the
output never said so, which left five `ok` lines and a traceback; the fixture
suite reported `ok` on an empty spec; `contains` searched the whole serialized
report, so its metric key asserted nothing and keying it to a name no checker
emits still passed — in the one assertion whose stated job is that a check failing
for the wrong reason has not passed. And `--repeat` is removed rather than fixed:
nothing looped, so it printed back the number the operator typed, which in a
document whose purpose is evidence is the worst possible field.

Every fix above was falsified by reintroducing the defect.

## 0.1.357 — the harness scored nothing, and the fixture was not a deliverable

Two defects in 0.1.356 and 0.1.355, both found by using them, and both instances
of failures this repository had already named and fixed elsewhere.

**`run_conformance.py score` scored nothing.** `score_checks` and `score_recall`
were defined and never called; `score` shared a branch with `run` and did exactly
what `run` does, then told the operator to go and run `score`. So the harness
whose stated purpose is *"scores every output with the same three check scripts"*
did not score. That is the dead-constant defect removed from `check_design.py`
five releases earlier — `TYPE_FLOOR_PX`, declared and never read — committed
again in the release that was meant to close the loop. `score` now walks the run
directory, finds each deliverable, runs `check_prose.py` and `check_design.py`
against it, keyword-scores the recall task, writes `scores.json`, and exits
non-zero on any failure. **A task that produced no artifact records `no
deliverable`, never a pass** — an agent that answered in chat instead of writing a
file is the most common real outcome, and it has to read as a failure to produce.

**`fixtures/deck-pass.en.html` did not pass.** It cleared `check_prose.py` and
`check_design.py` — the two CI can run — and failed `inspect_layout.py` with
three unmeasured checks and no focal element on 14 of 16 pages. A fixture named
`pass` that passes two of three checks is the same overclaim the checks exist to
prevent, and it was only visible because 0.1.355 deferred the browser check to a
local run and the local run was then actually performed. The fixture now carries
a stat band and a display lead, exercising `.band .k`, `.band .v` and the focal
element, and clears all three checkers at all three geometries with nothing
unmeasured.

**One genuine probe bug fell out of that.** `inspect_layout.py`'s measure-bar
candidate window — at least 120 long, 30 to 90 thick — was applied to *rendered*
pixels. A page is a zoom-scaled stage and a figure is scaled again into its cell,
so an identical bar measured 46 at 1280 and 28 at 794: the component-colour audit
accepted every bar in a document in landscape and rejected all of them at A4, for
a reason having nothing to do with the document. The window is a statement about
the *drawing*, so it now reads SVG user units — the units the figure was authored
in, which are the same at every geometry.

## 0.1.356 — the conformance harness, and an honest scoreboard

The last of the five releases. `scripts/run_conformance.py` runs a fixed task
suite through whichever agent CLIs are installed on the operator's machine and
scores every output with the same three check scripts, so the claim this package
makes — *one bar, whichever model wrote it* — has something behind it.

Three tasks, chosen because they are scorable without a judge:

- **T1 deck** — a six-page HTML deck on an invented subject, graded by
  `check_design.py` and `check_prose.py`. D12 and M4 must come back `ok`.
- **T2 de-AI rewrite** — a tracked passage seeded with six banned phrases, which
  must reach zero. Deterministic and model-portable: no taste involved.
- **T3 red-line recall** — five closed-form questions with a keyword answer key.
  **No LLM judge.** It tests the one cross-model property that can be scored
  mechanically: whether the rules were loaded and retained at all.

`conformance/CONFORMANCE.md` is the tracked scoreboard; `conformance/results/` is
gitignored, because raw agent output is a render and renders live with the run.
CI gains `run_conformance.py validate`, which parses the suite and nothing else —
it cannot invoke an agent, and must never look as though it did.

**The first run records one agent of twelve.** Claude Code is present, and the
scoreboard names the exact CLI build;
everything else on this machine reports `not installed — not exercised`, and two
platforms report why they can never be probed at all (Antigravity ships as an IDE
rather than a CLI; Kimi and DeepSeek are API chat models with no binary). That is
the honest state, and it is printed rather than omitted — an agent nobody ran is
not an agent that passed.

What the harness cannot do is stated in its own docstring and repeated in the
README, because the temptation to overclaim here is the whole risk. It cannot show
a model writes well: the checks measure mechanical conformance, and a page is done
when a human reads it as intentional. It cannot show reproducibility, because
agent CLIs are non-deterministic and their versions drift weekly, so a recorded
pass is one run of one version on one machine on one date and the report always
prints its `n`. And it does not run in CI.

The README's support claim is rewritten to match. It no longer says "works with"
a list of platforms; it says what is verified every push, what is only observed
per release, and what is not verified at all.

## 0.1.355 — the gates get tested

`check_prose.py`, `check_design.py` and `inspect_layout.py` decide whether a
deliverable is acceptable, and until now **none of them had ever been tested**.
They measure a deliverable, and the only deliverables this repository could reach
sat in the gitignored `docs/`, carrying a client name red line 9 bars from here.
So the machinery meant to make output quality portable across models was itself
unverified — which matters more as the number of platforms grows, because the
checks are the only thing that does not vary with the model.

Two tracked fixtures, both synthetic and client-free — a fictional metering
programme, `www.example.org` as the origin, no engagement fact anywhere:

- `fixtures/deck-pass.en.html` — 16 pages, 133 sentences, 16 titles. Every graded
  metric passes and both scripts exit 0.
- `fixtures/deck-broken.en.html` — the same deck with one named defect per metric:
  four banned phrases (M4), a literal hex outside the token block (D4), and a page
  whose footer states no handling terms (D12, the one design check that gates).

**The broken one is the point.** A suite proving only that clean input passes
cannot tell a working check from one that returns `ok` unconditionally — which is
exactly the defect 0.1.350 removed from `inspect_layout.py`, where every
reassuring line was the `else` branch of a defect test. `check_fixtures.py`
asserts *which finding fired*, not merely that the run failed, because a check
that fails for the wrong reason is not a check that passed.

`fixtures/expected.json` is hand-written and asserts **verdicts, not values** —
`M8_length_cv: "ok"`, never `0.578`. A golden file full of raw numbers rots on
every cosmetic change and teaches people to regenerate it unread; this way a
legitimate threshold change touches one line and reads in review as an intent
change, while an accidental regression reads as a verdict flip. It also carries
`forbid_verdicts: ["n/a"]`, so the passing fixture cannot quietly decay into a
document too thin to grade and report green for it.

The fixtures are generated by `scripts/build_fixtures.py`, which lifts the `:root`
block from `tokens/`: a fixture grading a document against a palette the skill no
longer ships is worse than no fixture. `--check` runs in CI.

Falsified: repairing the planted D12 defect makes the suite fail, so it is not
vacuous. `fixtures/README.md` records the rule that pays for all of this — **never
edit a fixture to make a check pass**. If a check fails on the passing deck, one
of the two is wrong; decide which and say so. Editing the evidence to match the
verdict is how a metric becomes decorative.

`inspect_layout.py` stays out of CI because it needs Chromium, and is run against
the fixtures locally.

## 0.1.354 — the per-platform artifacts become generated, and the package gets a front door

Twelve platforms, each wanting an install note; three wanting a pointer file at a
path their own convention dictates; two wanting a plugin manifest. Hand-written,
that is fifteen more copies of facts this repository already holds — and it has
shipped the consequence twice already: `adapters/claude-code.md` told people to
`git clone` into the skills directory while `README.md` insisted on a symlink
*because a copy had stranded at an old version*, and `AGENTS.md` carried a
withdrawn fill floor for four releases.

**`scripts/build_entrypoints.py` renders all eighteen of them** from
`adapters/platforms.json` and `SKILL.md`, with the `--check` mode this repository
already uses for `embed_font.py`, `embed_icons.py` and `build_geography.py`, and
the same failure sentence, so a stale tree reports as stale rather than as a
mystery. It runs in CI before `check_repo.py`, because a stale artifact must be
named as stale rather than surfacing as a puzzling guard failure.

Generated: the twelve `adapters/*.md`; `GEMINI.md`,
`.github/copilot-instructions.md` and `.cursor/rules/lumi-style.mdc`;
`.claude-plugin/plugin.json` and `marketplace.json`; and
`.well-known/skills/index.json`. The six red lines are **lifted from `SKILL.md`**
rather than paraphrased, because a pointer file that restates them is a seventh
copy waiting to drift.

**Deliberately not generated:** `SKILL.md`, `AGENTS.md`,
`prompts/lumi-style-core.md`, `references/`. Assembled prose is worse prose, and
the entry points a reader is most likely to actually read should be the ones a
person composed. The generator covers the artifacts whose content is *packaging* —
paths, invocations, manifests — where there is no judgement to lose. That is a
narrower claim than the plan for this release made, and the narrower claim is the
true one.

**The first cut of the pointer files was broken and the guards caught it.** All
three wrote `[SKILL.md](SKILL.md)`, which resolves to `.github/SKILL.md` from a
file in `.github/`. Links are now computed from each artifact's own depth. A
generator that emits the same mistake into every file has made the breakage
uniform rather than impossible; the markdown-link guard is what noticed.

CI also gains `inspect_layout.py` in its `py_compile` list, which it has never
been in — the largest script in `scripts/` had no syntax coverage at all.

Still to come: tested fixtures (0.1.355), and the cross-agent conformance harness
(0.1.356). No claim of cross-agent verification is made yet, because none has been
performed.

## 0.1.353 — a withdrawn number may not be restated as though it still binds

`tokens/design-tokens.json` gains a **`retired` register**: the values this rule
set withdrew, each with the release that withdrew it and why. A withdrawn number
has to be *stated* somewhere or no machine can tell it from a number deleted by
accident, and this repository's documented worst drift is exactly that — the 82%
page-fill floor and the 11px type floor were withdrawn in 0.1.340 and went on
living in two entry points for four more versions, invisible because nothing
compared the copies.

`check_repo.py` gains **`retired values`**: every paragraph restating a retired
number must mark it as retired. It reads the register rather than a hand-written
list of things an entry point should not say, which is the direction of authority
CLAUDE.md requires — a check that asserts its own expectations is a second source
of truth.

Two things the first cut got wrong, both caught before it shipped:

**Line scope was the wrong unit.** This prose is hard-wrapped, so "Withdrawn in
0.1.340 … the 11px type floor" straddles two lines, and a line-scoped check
reported the second half as an unmarked restatement — twelve false positives on a
clean repository. A sentence is the unit a reader reads, so it is the unit the
marker has to be found in.

**A bare number is not a rule.** `40%` names the withdrawn D9 share cap in one
sentence and "four diagrams rendered at 40% of their cell" in another. Same
digits, opposite claims. Each retired entry now carries `context` phrases, and a
value counts as a restatement only alongside one of them; an entry with no context
list fails rather than guessing. The guard also reports a waiver that no longer
matches anything, which is how the one waiver this needed came to be deleted —
once `context` landed, the sentence sizing an icon against an 11px caption stopped
looking like a floor claim at all. A waiver that survives its cause is a standing
permission nobody re-reads.

What it cannot do: tell whether a rule's polarity changed while its digits stayed.
"3-6 word headline" as a ceiling and as a target are the same characters, and
CLAUDE.md rule 4 exists because that has cost three regressions. That stays with
the reviewer.

## 0.1.352 — the platforms get a registry, and a withdrawn floor stops shipping

First of five releases making this skill work across many agents. This one adds
no platform support by itself; it makes the current state *checkable* before it
changes, which is the only order in which adding twelve platforms is safe.

**A floor withdrawn twelve releases ago was still shipping.** `design-rules.md` 1
and `eval-rubric.md` both record that 0.1.340 withdrew the 11px type floor as
invented without an ask. `tokens/design-tokens.json` went on declaring
`size_floor_px: 11` under a note asserting it *"binds every text run except
chart_scale_px.source"*, and `lumi-theme.css` went on calling the same value
`--fs-floor`. CLAUDE.md makes the tokens win on conflict, so the authority
mandated a floor the rules had retired, and every deliverable built from the
token block inherited it. The value stays — it is the smallest size the scale
uses — under the name it deserves: `--fs-fine`, `size_smallest_px`, with the
binding claim withdrawn. `check_design.py` also carried `TYPE_FLOOR_PX` and
`SOURCE_FLOOR_PX`, defined and never read since 0.1.340; a constant naming a
withdrawn rule is a trap, because the next person needing a threshold finds one
already declared and wires it up.

**`adapters/platforms.json` — one place platform facts live.** Twelve platforms,
each with its install paths, capability tier, entry file and install note. The
facts had been spread across four hand-written notes and a README table, and they
had already disagreed: `adapters/claude-code.md` said `git clone` into the skills
directory while `README.md` insisted on a symlink *because a copy had stranded at
0.1.334 while the repo reached 0.1.337*. Two files, one fact, opposite
instructions.

Three capability tiers, because the axis that matters is not which vendor an
agent comes from but what it can do: `full` reads the bundled files and runs the
scripts, `files` reads but cannot execute, `prompt` gets one pasted context and
no tools. What verification means differs per tier, and an agent that cannot run
the checks may not call a deliverable verified.

**Most of these platforms already worked; nobody had said so.** `~/.agents/skills/`
turns out to be a convergent location — Gemini CLI, GitHub Copilot, OpenCode,
OpenClaw and Pi all read it, and Gemini CLI gives it precedence over its own
directory — so one install serves five. Google Antigravity's workspace path is
`.agent/skills/`, singular, and is deliberately recorded as *not* the same
convention. Eight install notes join the four that existed.

**Two guards.** `platform manifest` requires every registry claim to have a file
behind it, every install note to be claimed by a platform, and every unverified
claim to carry its own written reason — Hermes ships with `path_verified: false`
and a waiver naming exactly what is unconfirmed, rather than an invented path.
`version citations` closes a gap this repo has had since it had entry points:
only `SKILL.md`'s frontmatter version was ever checked, so `AGENTS.md` carried no
stamp at all and the core prompt's self-declared snapshot line was unverified —
the two files that had already shipped four versions of drift. It also requires
every version cited anywhere to name a release some heading defines, which is the
drift CLAUDE.md calls this repo's worst.

Still to come: the numeric-claim guard (0.1.353), generated entry points and the
plugin manifests (0.1.354), tested fixtures (0.1.355), and the cross-agent
conformance harness (0.1.356). No claim of cross-agent verification is made here,
because none has been performed.

## 0.1.351 — the history moves onto the 0.1.x scheme

0.1.350 restarted the numbering but left the 22 releases behind it on the old
1.0.0 → 3.4.0 scale, so a public repository advertised two schemes at once and its
newest entry sorted below its oldest. They now occupy **0.1.328 – 0.1.349** in
their original order, running contiguously into 0.1.350.

**The citations moved in the same pass, which is the part that could have gone
wrong.** This repository names versions constantly — "since 0.1.339", "0.1.346's
register", "0.1.332's headline" — and those names are load-bearing: they are how a
rule carries the defect that produced it. All **165** references across
`references/`, `tokens/`, `scripts/`, the three entry points and `README.md` were
rewritten together, and every version cited anywhere in the repository now
resolves to a heading in this file. A citation naming a version no heading defines
is exactly the drift the checks cannot see, so it was verified explicitly rather
than assumed.

**Git history was deliberately not touched.** Commit subjects and the merged pull
requests still read `3.4.0 — one role, one rendering`, because rewriting 22
commits means force-pushing a public branch: every clone breaks and PRs #17–26
detach from their commits. The CHANGELOG is the canonical record; the git log is a
factual account of what each release was called when it landed. The same applies
outward — a deliverable exported before this carries a 3.x stamp that no longer
names anything here.

*No rule changed. This is bookkeeping, and it takes a version of its own because
the convention says a revision gets an entry and a bump — including the revision
that edits the convention.*

## 0.1.350 — a check that did not run is not a check that passed

**The version scheme changed with this release.** The package had been climbing
into a fourth major version, which read as a maturity it has not earned; 0.x says
plainly that
this is still pre-stable. From here the **patch position** carries ordinary
releases (0.1.351, 0.1.352, …), and the minor moves only for a change that would
break a deliverable built on the previous one. *(The releases before this one were
renumbered onto the scheme in 0.1.351, the entry above.)*

A review of 0.1.349 asked whether the layout probe establishes complete check
factors for a **new** document. It does not, and the way it failed is worse than
a gap: every reassuring line it printed was the `else` branch of a defect test,
so a check with nothing to examine reported the same thing as a check that found
nothing wrong.

**A document with no recognisable pages passed.** Run on an HTML file with no
`section.page`, the probe printed eleven affirmative lines — "one horizon on each
of **0 pages**", "all 0 pages hold 16:9" — and exited 0. Hidden pages passed too:
a zero-size page has `overflow` of −720 (not > 1), zero frame skew, one horizon
because `.foot` is still in the DOM, and an aspect of `0/0`, which no `>`
threshold is ever true for. Three `display:none` pages were credited as three
passing pages on every line.

**Coverage was a property of class names, not of the design system.** Measured on
two documents identical apart from their class names: ten role checks became two.
Six of the ten selectors — `.t .sup .eyebrow .k .n .listhead` — appeared nowhere
in `tokens/`; they had been read out of a deliverable. A document built from the
token files the skill tells an author to copy therefore matched two roles, lost
the other eight **without printing a word**, and the focal check *inverted*: with
no `.t` to exclude, the title became the page's focal element and a flat page
passed. Renaming a class made the report shorter and greener.

The fix is in both halves. The role vocabulary now ships in
`tokens/lumi-layouts.css` as a declared contract, and every check that finds
nothing says `NOT MEASURED` with the reason and the selector it wanted.
`inspect_layout.py` **exits 1 when anything could not be measured** — the design
judgements still gate nothing, which is the whole distinction: reporting that a
check did not run is not a judgement about the page. `check_design.py` has had
this concept since 0.1.339, in the same directory, while this script expressed all
five of its failure paths as silence.

**Three checks were measuring the box instead of the thing in it** — the mistake
0.1.349 was written to catch, committed by 0.1.349's own additions. The title role
ignored size, to excuse a cover legitimately larger than a content page, so 34px
and 57.6px produced the same key and the first defect the audit was built for was
undetectable by it; a title is now three registers, each compared on size. The
band-baseline check compared element boxes, and a value written the shipped way —
`41<span class="u">%</span>` — sits in a box 25px deeper than one without a unit
while the digits stay on one baseline, so it flagged bands whose numbers were
exactly aligned. Centerpiece scale, cell fill, the empty-band scan and the
collision probe all used `getBoundingClientRect()`, so a grown SVG box inflated
the scale *and* filled the empty-band scan with phantom ink at the same time.

**The consistency and ground audits only ever ran at 1280×720.** Run at A4 — a
required matrix point since 0.1.340 — the same probe found the callout at
**12 / 13 / 11.5px**, set per context by the portrait block of the token file that
carries the rule against it, and the strong ground tier breaking its own 1.40:1
ceiling on two independent documents. Both audits now run at every requested
geometry and say which one they ran at; `--ground-strong` drops .25 → .20, which
measures 1.369 where .21 measured 1.396 and left no room for a document's own
ground drawing.

**Two rules mandated mechanisms the package does not ship**, the failure mode
`CLAUDE.md` §5 exists for and now the fourth and fifth instances. The title-block
reserve that holds the content datum shipped in a deliverable and not in
`tokens/`, so every document built from the tokens kept the floating lede the
rule bans. And `box-sizing: border-box` shipped nowhere, while the layouts file
declares fixed 1280×720 and 794×1123 stages that are arithmetic nonsense without
it — measured on a fresh document, **all six pages +72px**, page-height
conformance being the first thing §7 says to check. `.lead .v` also asked for
`var(--display, var(--sans))`, and neither token has ever existed, so the one
number that *is* the page silently inherited the body face.

Smaller, all found by using the thing: a missing Pillow deleted the ground audit
rather than reporting it; a crashed consistency probe printed nothing at all and
`--json` omitted three audits entirely; two files in one run overwrote each
other's contact sheet, which the docstring calls the real output; the `ImportError`
message advised `--no-sheet`, which does not help because the import happens
either way; `contact_sheet` documented a `sips`/`montage` shell-out that was never
written, and `subprocess` was imported for it; nothing waited on `document.fonts`
or listened for the document's own errors, so a report could be measured against
fallback metrics and printed as fact; and `--dark` was read only to name output
files while nothing switched the palette.

Two false alarms went the other way and were fixed with the same discipline: a
band that stacks in portrait is not 338px out of line, and a figure deliberately
hidden by the landscape/portrait pair is not an unreadable drawing.

## 0.1.349 — one role, one rendering: a consistency system, and the probe that holds it

A reader asked for a complete consistency audit of all 30 pages and for the
confirmed style to live in the tool rather than in my head. They named four
inconsistencies. Measuring every repeated role across every page found those four
**and two more**, one deeper than anything reported.

**The title rendered three ways** — content 34px/700, cover 57.6px/700, and the
**closing at weight 400**: the register reached every page in 0.1.346 except the
last one. **The callout rendered three ways**, 12 / 12.5 / 13.5px, unreported —
residue from three rounds of per-page density fixes, each locally right and the
accumulation exactly the inconsistency a reader can see. That produced a rule: **a
page that no longer fits gets its content trimmed, never its type nudged.**

**The deepest defect was not on the list.** Titles all began at the same y, but the
support line began at three different heights and the first content cell at **ten,
106px to 219px**. Content started somewhere different on almost every page, which
is what a reader feels flipping through even when every type style matches. The
title block now reserves a fixed height derived from the line-heights, and content
begins at **198px on all 26 content pages**. Six support lines were trimmed to two
lines and one glossary page went from twelve terms to ten to pay for it — content,
not type. The datum is per geometry: portrait releases it, because portrait is a
composition and not a reflow.

**The stat band was 17px out of line.** Two causes, both mine: the lime highlight
replaced the band cell's padding, making the headline number's box 40px where its
neighbours were 80px; and the band centred each cell, so a label that wrapped one
line further lifted its own number. The highlight now paints the *text*, and a
band aligns at the top — it is a row of comparable things.

**Two comparison bars, two greens.** This was a collision between two of these
rules — *one lime event per page* met *the same component always looks the same* —
and the component lost. Resolved as a rule: **the lime marks a number panel, never
a chart mark.** A chart mark encodes a value a reader compares across pages. A page
with no number panel simply has no lime.

**The probe is the general form, not four checks.** `inspect_layout.py` now reads
the deck as a system: for every repeated role it collects the computed family,
weight, size, transform, tracking and colour and counts distinct renderings, with
every sanctioned exception **declared in the probe** rather than tolerated. Plus
one datum, one colour per chart component, and a shared band baseline. Tracking is
normalised to em first — it is authored in em and computes to px, so two sizes can
never agree otherwise, which cost a round of chasing a difference that was not
there.

Known and reported rather than fixed: at **1800x1000**, an off-design shape kept
deliberately in the probe set, three pages still show small collisions and two
spill by under 8 page-units. Text rewraps at that zoom. Both design geometries are
clean.

## 0.1.348 — the working green and the event green, numbers that rank, a quieter cover

Six items from a review. One needed measurement rather than taste, two were
defects, and both defects were invisible to the probe added one release earlier.

**Can the new green be used everywhere on content pages?** No, and the usage
counts say why. The accent appears there **84 times as a fill, 71 times as a
stroke, 23 times as a wash, and 0 times as text**. The lime cannot do the strokes:
1.21:1 on white makes a chart rule, a connector or a decision outline invisible,
and §1 already counts a mark a reader must tell apart as text. It could do the
fills, but 84 acid panels is the opposite of non-contention and destroys the thing
that makes it an event. So the two greens are named for the two jobs the canvas
forces apart: **`--acc` forest is the working green** — anything that must read on
white — and **`--lime` is the event green** — large panels only. Collapsing them
into one would take a dark content canvas, declined in 0.1.346.

**The collision probe only knew one kind of collision.** 0.1.347 added it after a
reader found text on text; it compares text to text and nothing else. The same
reader immediately found two defects it could not see, and measuring text against
*drawn* elements found **11 pairs**: a field sitting 22px on a paragraph, and the
globe crossing `DATE`, `VERSION` and `CLASSIFICATION` on both the cover and the
closing. It now compares text against every drawn element — field, figure, band,
spec, geography — with containment excluded, because a caption inside its own
figure is not a collision.

**The catalogue field is removed from page 3.** Its label was cut in 0.1.347 to fix
a different collision, and unlabelled the 161 marks read as texture rather than as
evidence — which is exactly what the reader called them. The stat band on that
page already says 161. The field survives where it earns its place: the
thirty-page tier strip, where the distribution *is* the argument and no number
states it. A signature device used twice, once meaningfully and once not, is used
once.

**Key numbers rank in three steps and are set like arguments.** `.band .v` was
weight **400** — a caption with large type. It is now the display weight, and
importance is three tiers rather than a single highlight: the number the page
turns on gets a **lime panel** with near-black numerals (16.44:1), its support is
**forest**, and context is **ink**. One lime panel per page, because ΔE against
the forest is 94 and two greens on one page would read as two meanings.

**The cover and closing get quieter.** Both subtitles are gone — the title is the
page. The source clause is cut from the cover colophon, after verifying `D6` still
finds the document's provenance on the closing. The build stamp now appears
**once**, in the closing colophon: `SKILL.md`'s version-lockstep rule said cover
*and* closing, so the rule moved with the deck rather than being quietly broken.
The document attributes are retained and stop competing — out from under the globe
into one narrow mono column in the clear lower-left. The closing title takes the
cover's register.

One self-inflicted defect on the way: the new number tier was first called
`.v.lead`, which collides with `.lead`, the focal block. D1's surface discovery
keys on class tokens, so it began grading every focal element against the lime
panel — five false contrast failures on the dark palette. Renamed to `.v.first`.
**A class name is an interface.**

## 0.1.347 — text on text, the display pulled back, and one lime event in the body

A reader reviewing 0.1.346 found characters overlapping at the bottom of two pages,
asked for the display type 30% smaller, and asked whether the acid green could
appear once inside the body rather than only on the part openers.

**The overlaps were real and neither existing probe could see them.** Every check
in `inspect_layout.py` measures a block against the *page* — its top, its bottom,
its column, the footer rule — so two blocks landing on each other in the middle of
a page is invisible to all of them. The cover's support paragraph sat 34px into
the spec strip and the catalogue page's stat labels sat 48px into the paragraph
below. One cause: **0.1.346's heavier register outgrew grid rows sized for the old
one**, so a block overflowed its track onto the next instead of lengthening its
own. `min-content` on those rows fixes it, and that is now a rule — when the type
scale moves, the tracks that hold it move with it.

A **text-collision probe** joins the set: leaf text against leaf text, since a
container legitimately encloses its children. Confirmed by restoring the old
`hero-band` row definition and watching it fire.

**Display type is down 30%** — `clamp(64px, 9vw, 132px)` to
`clamp(45px, 6.3vw, 92px)`. Big enough to be the event, not so big the page
becomes a poster with a caption.

**One lime event per body page, and it is a fill.** The deck's single most
important number — code intersection at 100% — is now an acid-lime bar with
near-black numerals. Measured, because "is this comfortable to read" deserves an
answer rather than an opinion: the panel's edge against the canvas is **1.21:1**,
so it *glows rather than cuts*; near-black on it is **16.44:1**; at **chroma 102**
it is right at panel size and would be harsh as a hairline or as small text, so it
is never a rule or a caption. Once per page, because ΔE against the semantic
forest is **94** — plainly a different colour, and two greens on one page would
read as two meanings.

Ground tiers unchanged at the reader's request.

## 0.1.346 — the ground, the acid green, and type that commits

The reader asked for water and light behind every page, and pointed at
`silviamalavasi.com` for the green and the register. I read that site with a
headless browser rather than from its rendered text, because the markdown
conversion returns one line of copy and nothing else.

What it actually is: canvas `#0A0907`, paper `#F2EDE4`, **the green `#B8FF00`**
across 91 text uses, plus magenta, yellow and red. Type is Inter with **245
elements at weight 700 and 52 at weight 900** against only 57 at 400; display at
254px and 120px, line-height ~0.9, and letter-spacing `normal` everywhere.

**Two measurements shaped the release.** `#B8FF00` measures **1.21:1 as text on
LUMI's white canvas** — unreadable — and 16.44:1 with near-black reversed out of
it. That site is dark-canvas-first and its palette depends on it. LUMI stays
light-first, so **the lime is a surface and never light-canvas text**, which is
how that site uses its yellow and magenta anyway. And **we ship D-DIN Regular and
Bold and nothing else**: Inter is not vendored, no font tooling is installed, and
the system faces cannot be redistributed. No rule names a face the package does
not carry — `CLAUDE.md` §5, written after 0.1.332 required a display face, shipped
none, and rendered nothing for five releases.

**The ground, and the rule that lets it exist.** `brand.md` says a field with
nothing behind it is decoration and decoration is contention. A background
texture *is* decoration. It resolves on one distinction, now the rule:

> A field is discrete and countable; a ground is continuous and uncountable. If a
> reader can count the marks, every mark must mean something. If there is nothing
> to count, there is nothing to misread — so a ground may be decorative precisely
> because it can never be mistaken for evidence.

Its honesty test is therefore different in kind, and both halves are measured: it
may never exceed **1.40:1** against its canvas, and it may never resolve into
repeated identical marks. The contrast is measured on the **rendered** page with
every foreground element hidden — and that mattered: the three tiers were tuned
analytically, measured at **1.428 and 1.549**, and had to come back down. The
probe caught its own author.

The flows crowd **below the waterline** and thin out above it, so the air where
the claim lives stays clear. That is what makes the ground structural rather than
wallpaper, and it is also what answers "it must not overpower the content" with a
number instead of an opinion. The wider hue range — lime, forest, teal, blue,
gradients along each line — lives here, safely, because the ground cannot be read
as data. The foreground stays one colour, one meaning.

**The register commits.** Display to `clamp(64px, 9vw, 132px)` at weight 700 with
0.92 leading; page titles from 22px/400 to 34px/**700**; support lines from
14.5px to 16px/500 so the subtitle is a second voice rather than small print;
lead numerals to 116px; figure numerals bold. `.3em` eyebrow tracking is gone —
the most dated device in the deck, and the reference tracks nothing anywhere. The
part openers are now full **lime fields** with the claim in near-black at display
size, and they are the only pages in the deck that are.

Three probes added, each confirmed by making it fail: the ground's rendered
contrast ceiling, the ground-is-countable test (fired on a ground built from
eight identical rects), and **D13**, which forbids the lime as light-canvas text.
D13 had to be rewritten to scan the raw CSS after the first version silently
passed the exact case it was written for — the rule map merges duplicate
selectors and a later `.sup` in a media query dropped the declaration. A guard you
cannot make fire is not a guard.

The ground also had to be excluded from every ink measurement. It is behind
everything and covers the page, so on first render all thirty pages reported that
they ran past their own footer rule.

## 0.1.345 — the water thesis: LUMI gets a brand, and the skill finally says what to reach for

Four rounds of review made this skill measurably more correct and no more alive.
The reader said the same thing four times. Two measurements say why.

**The rule set was 23 : 1 brakes to accelerators** — 272 lines that restrict
against 12 that invite. A documented study of this exact failure mode
(`impeccable.style/research`, ~30 skill iterations, ~200 sampled concepts) found
that **5 : 1 produced "65% commitment, and 65% commitment is what bland looks
like"**, and that inverting the order — land fully committed first, then make it
clear — was "the biggest single quality jump" in the whole study. This repo ran
nearly five times more braked than the ratio that already produced bland, and
every release had added more, because every release fixed a defect a reader found.
Nothing was ever added on the other side.

**And there was no brand.** `references/` held writing rules, storyline templates,
design rules and an eval rubric — all craft, no identity. The word "brand"
appeared once in the entire rule set, and it said branding was subordinate to
data. A style guide answers *is this correct*; a brand answers *what is this, and
why does it look like nothing else*. Only one of those had ever been asked here.

**`references/brand.md` is new and it loads first.** The thesis is
`上善若水，水利万物而不争`, and three of its four parts were already true of what
LUMI does — one of them already in the source code. One apparatus serves every
industry the way water takes the shape of any vessel. LUMI declines where others
claim: click-through never measures relevance, no accuracy figure before the
golden set, AI never signs, a refusal is honoured by hand — that is not modesty,
it is *we are the one you can check*. LUMI is light, and you cannot see a current,
only the light on it.

**Two structural devices**, because "committed skin hides template bones" — a
fully-committed surface on a standard grid is the trap:

- **The field** — many small marks at varying intensity, one per datum, ordered by
  the data's own sequence. The deck was already drawing this by accident in the
  tier strip and the stat bands. Page 3 now carries the whole catalogue as 161
  marks, 121 on the automated chain and 40 off it because those sources refused.
  **A field with nothing behind it is decoration**, so every mark declares its
  datum and `inspect_layout.py` fails a field whose marks outnumber its data. That
  is the one new brake this release adds, and it is what keeps the shimmer honest.
- **The waterline** — one horizon per page: air above, record below. The footer
  hairline stops being a border closing a box and becomes the surface the page
  sits on. Two horizons is stripes, none is a document; exactly one is checked.

**The accent gains a five-step ramp** for fields and surfaces. It carries no
meaning — one colour one meaning still governs data, and those tokens stay flat
and measurable. Keeping the two jobs in separate tokens is what lets the brand
shimmer without the data lying. Every step was measured on both canvases and every
one carries text: 5.93 / 4.54 / 6.52 / 9.18 / 12.32 on light, 5.61 / 4.69 / 6.67 /
9.70 / 13.46 on dark.

**The ratio moved from 23 : 1 to 9.1 : 1 — and brakes went up, not down**, from
272 to 309. Nothing was deleted; all of it is hard-won defect history and all of
it still applies. What changed is that the skill now says what to reach for, and
the brakes apply at step 4 instead of framing step 0. Still roughly twice the
ratio the study used, so this is a direction and not a destination.

The English-only guard was tightened while doing it. The allowlist was per file,
which is too coarse in both directions — it let prose drift into an allowlisted
file and forced a whole file onto the list for one quoted line. CJK is now
permitted inside backticks or a fenced block and nowhere else, which is exactly
the distinction the red line always meant.

## 0.1.344 — handling terms on every page, provenance once per document, and one table per page

A reader asked for four things and two of them were defects the checks had just
been rebuilt to catch and still missed.

**Per-page source lines go, for sales and marketing.** A source under every figure
and again in every footer is apparatus a customs manager does not need, and it was
occupying the line a commercial document does need. Provenance moves to the cover
and the closing, where it is read once instead of skipped thirty times. Red line 1
is unchanged — no invented facts, every number still traces. **Genre-scoped**:
consulting deliverables and internal analysis keep per-page sourcing, because
there the reader is auditing the claim rather than being sold to. `D6` now asks
the document for provenance instead of asking every footer.

**Every page carries handling terms and where the document is from.** Left of the
footer rule: the confidentiality line and the organisation's site; right: the page
number. Pages travel alone — a slide is screenshotted out of a deck and forwarded
without the cover. `check_design.py` gains **D12, the one design check that fails
the run**. Everything else there reports, because a page is done when a human
reads it as intentional and a threshold satisfiable without improving the page
ends the looking. D12 is different in kind: not a judgement about whether a page
is well made, but a commercial requirement on the artifact. A design metric that
gates is a mistake; a commercial one that does not is a different mistake.

**Two tables side by side is two documents on one page.** A grid claims its cells
are comparable along the axis its header names; two grids with different columns
and different row counts share no axis, so their rows can never align and a reader
sees the misalignment before they can name it. That page is now one drawing — the
deck's own thirty pages as a strip, each tick coloured by whether it is client
safe, needs adapting, or never leaves the building — over three numbered steps.
16 / 10 / 4. `inspect_layout.py` reports any page carrying more than one table.

**The 4px that made two columns look wrong was `.lead + *`.** In a grid, the
adjacent sibling is **the next column**, not the block below, so an unscoped rule
put a 4px top margin on the first cell of every page whose lead spanned the row —
six pages with one column sitting low. An adjacent-sibling selector inside a grid
container is almost always a mistake.

**And the spill probe was asking the box again.** `scrollHeight` on an
`overflow: visible` box **does not count children that spill out of it**: it
returned exactly zero while two pages ran 26px and 8px past their footer rule.
That is the third probe in three releases to measure a container instead of its
contents. It now measures the deepest ink against the footer rule.

Distances are reported in **page units, not device pixels**. Once the page is a
scaled stage a device pixel is not the unit of the design, and the same layout was
reporting 3px of skew at one window size and 4px at another — a threshold that
silently tightened as the window grew.

## 0.1.343 — the page becomes a page, and a probe stops verifying its own setup

A reader suspected the landscape page was not 16:9, asked why the layout tool had
not caught it, and marked three more things on four screenshots. The suspicion was
right, the tool could never have caught it, and the three marks turned out to be
one cause.

**The page was whatever shape the window was.** `.page` was `min-height: 100svh`
with no aspect lock anywhere: 16:9 at 1280x720, **4:3 at 1280x960**, 1.6:1 at
1440x900. The surplus height was the dead band above the footer that the reader
circled. Landscape is now a fixed **1280x720** stage and A4 a fixed **794x1123**
sheet, each scaled to fit with `zoom` and letterboxed in a gutter that never holds
page content. `zoom` rather than `transform`, because zoom participates in layout,
so pages still stack, scroll and snap.

**The probe could not have caught it, and the reason is the most important line in
this release.** `inspect_layout.py` set the viewport to 1280x720 and then measured
`section.height - window.innerHeight` on a `100svh` page: **zero by construction**,
on every page, in every run since it was written. "All 30 pages are exactly 720px"
meant "the page filled the window I made 720px tall". It had never tested the
aspect ratio at all. **A probe that establishes the condition it verifies proves
nothing** now leads the verification section of `design-rules.md` §7 and the
rubric, above "a probe that has never failed is not a probe". The new aspect probe
renders five window shapes chosen because they are *not* the design geometry.

Locking the geometry moved the blind spot rather than removing it: a fixed box does
not grow when its content does, it spills, and the height probe would report zero
while the page was visibly broken. A content-spill probe measures `scrollHeight`
against `clientHeight`, confirmed by shrinking the stage to 620px and watching four
pages fire.

**Three of the reader's four marks were one cause.** `.fig svg` was `flex: 1 1 0`,
so the box grew into all leftover height and `preserveAspectRatio` centred the
drawing inside it. Measured: the first mark sat **79-185px below the top of its own
box**, and the caption **95-205px below the drawing**. That is why six pages read
as "columns not level" while the column probe reported 0px — **it compared element
boxes and the reader was looking at ink**. Column tops and weight now map an SVG's
`getBBox()` through its CTM. The drawing takes its own aspect, ten viewBoxes were
trimmed to the art they hold, and the caption's doubled spacing (a gap on `.fig`
and a margin on `.cap`) became one.

**A page states its source once.** Thirteen figure pages carried both a figure
source line and a footer one; eleven cited overlapping sections and two were
identical word for word. The figure's line wins, and the footer keeps a source only
when it says something the figure's cannot.

**And the deck got a voice.** Asked how 0.1.342 answered "no visual impact,
mediocre, flat", the honest answer was that it fixed hierarchy and structure, not
brand presence — and that nothing could be composed to a frame while there was no
frame. With one: the two part openers are full accent fields with the claim
reversed out, and the cover's globe is height-led and bleeds off the right edge
instead of sitting beside the type as an ornament.

Three checker defects surfaced doing it. `D1` graded every colour against `--bg`
and `--card-bg` because those were the only surfaces the deck had; it now
discovers painted surfaces by reading the CSS, composites translucent washes onto
the canvas first, and grades a rule that declares its own background against that
background. That found two real defects invisible since 0.1.338: **amber measured
4.68 against a canvas it never touches and 4.24 against the wash it actually sits
on**, and the dark seal the same. Both moved. `D6` asked the footer for a source
line; it now asks the page.

## 0.1.342 — a focal element on every page, a table only for values, and probes for both

A reader called all 28 pages flat, mediocre and without visual impact, named the
split layouts as ugly, said far too many tables carried non-numeric information,
and pointed at one figure caption as plainly odd. Every one of the four was
measurable, and three had a single mechanical cause.

**The flatness had a number: 24 of 28 pages carried nothing larger than 15px body
copy.** Only the cover and two stat-band pages had any display tier at all. A page
with no entry point gets read top-left like a document instead of looked at. Every
page now has one focal element — a display number with its gloss, a claim at
display size, or a figure composed to dominate — chosen per page, and half the
pages got a redrawn figure rather than a number. A display tier (`--fs-lead`,
`--fs-lead-xl`, `--fs-say`) and a `.lead` block ship in `tokens/`. **There is no
floor on it**, and there will not be one: a threshold would push a number onto a
page whose figure already carries it, which is the 82% fill floor's mistake in a
new costume.

**Fourteen of sixteen tables held prose, not values** — digit density at or below
2%, including a literal two-by-two truth table laid out as four rows and three
pages whose "table" was a tempting sentence beside a safer one. A grid claims its
cells are comparable along the axis its header names, and sentences make that
claim false. They are now a timeline, a relay, a two-by-two, three maturity cards,
a veto diagram, two graded ladders, numbered vows and paired swaps. A scoring form
stayed a form.

**The split layouts were ugly for one reason, and it was a specificity bug.**
`lumi-layouts.css` had said `.body.split > div { justify-content: flex-start }`
since 0.1.339 and it had **never once applied**: the fill rule above it reaches
(0,6,1) because every `:not()` contributes its argument, against that selector's
(0,2,1). Twelve of fifteen multi-column pages centred their columns independently
and drifted by up to 132px. One line fixed twelve pages. The same chain has since
won two more arguments it should not have.

**The odd caption was a duplicate.** Two of its four sentences appeared verbatim in
the same page's right-hand column, and a second page's 124-word caption restated
that page's entire ordered list. Below a figure now goes the number, its
conclusion name and the source line, and nothing else; explanation moves into the
page's own column where it is set at reading size beside the argument it serves.
Eight caption prose blocks retired.

Two part-opener statement pages join the deck — one line at display scale saying
where the reader is and what the next run of pages argues. A navigation rail
cannot do that at a glance, and the quiet page is what makes the dense ones read
as dense on purpose.

Six probes join `inspect_layout.py`, each confirmed by reintroducing the defect it
was written for: column tops, column weight, focal ratio, caption budget and
duplication, table census, figure share. Three of them were wrong within a day of
being written — two because their selector did not know a new block class, and one
because it counted a table stretched to 100% of its cell as a dominant figure,
which is D7's own failure reproduced inside the tool built to replace it. **A probe
is only as good as its vocabulary** is now recorded in the rubric.

Three checker defects fixed while measuring: `check_design.py` read `&#183;` as a
literal hex colour, and required a support line on pages whose display lead does
that job better; `check_prose.py` counted only `<ul>/<ol>`, so M10 measured three
enumerations on a deck that enumerates constantly in named blocks and reported a
66.7% triad rate off a sample of three.

Also corrected: `AGENTS.md` and `prompts/lumi-style-core.md` still carried the
82% fill floor and the 11px type floor, both withdrawn in 0.1.340, and the core
prompt still described the pre-0.1.340 cream and near-black canvases, the fixed
legend position and the retired caption description. That is four versions of
semantic drift in the two entry points the checks cannot read.

## 0.1.341 — the measure cap belonged to the page, not to one of its children

`.body` carried `max-width: 1180px` and `.foot` carried nothing. On the design
page that is invisible, because 1180 plus the padding is the page. On any wider
window the footer ran to the window edge while the composition stayed anchored
left, so **all 28 pages showed a dead band down the right** and the source line no
longer lined up with the content it sourced. A reader caught it at 1817px; the
contact sheet never would have, because `inspect_layout.py` renders at exactly
1280x720 and 794x1123, where the defect does not exist.

The cap is right — prose should not widen to fill a monitor. Applying it to one of
the page's three children was the defect. Anything sharing the page frame now takes
the same width and centers, so the leftover space becomes a symmetric margin
instead of a hole. Verified at 1280, 1817 and 1920: 28 of 28 pages align, and the
right margin equals the left.

Lesson recorded in `references/design-rules.md` §7: a probe that only ever renders
the design geometry cannot see a defect that only appears away from it. Check one
size the document was not designed for.

## 0.1.340 — 2026-08-07

Reader review scored H1, H2 and H3 at **1**, against self-scores of 3. The anchors
for 1 are "the page talks to itself", "a template forced onto the content" and
"figures are decoration". All three were fair, and the root cause is one sentence:
**0.1.339 turned qualitative design feedback into metrics and then optimised the
metrics instead of designing the pages.**

**Principles now govern.** `SKILL.md` opens with the principal-designer role and
four hard rules, above every mechanical rule in `references/`: design per page; no
new universal size floors without an explicit ask; verify on rendered geometry and
content weight, never the element box alone; if a page looks empty, redraw or
recompose rather than growing chrome. **Done when a human reads the page as
intentional — passing metrics is necessary but never sufficient.**

**Three invented floors withdrawn.** D7 (82% page fill), D9's 40% layout-share cap,
and the 11px type floor. D7 is the cautionary one: it measured the bounding box of
all ink, so a small chart with a long caption scored as full, and it was satisfied
by stretching table rows while four diagrams rendered at 40% of their cell. The
skill already forbade this move on the prose side — click-through must never
measure relevance, because the metric rewards what it exists to suppress. D7 was
the same mistake in the design half. **The whole D-series stops gating**;
`check_design.py` reports and exits 0.

**Two output geometries are now a governing principle**, both latent defaults for
internal and market material: 16:9 landscape at 1280×720 (primary, checked at
1920×1080) for projection and PDF/PPT export, and A4 portrait at 794×1123 for
printing and binding. Portrait is a composition, not a reflow; collapsing every
horizontal layout at a width breakpoint is the landscape design giving up.

**`scripts/inspect_layout.py`** renders a deliverable page by page at both
geometries and emits a **contact sheet** — the whole deck as one image, which is
what makes human review of 27 pages possible at all — plus centerpiece scale,
figure-to-cell aspect, and the largest empty band. It gates nothing. Its own first
version shot the viewport after a smooth scroll and produced a sheet of half-pages
under the wrong captions; it screenshots the section element now.

What the tool found immediately, and D7 had hidden: four diagrams at 4.6–5.4:1
sitting in 2.4:1 cells and filling 44–51% of the available height, two pages with
centerpieces at 13–15% and empty bands over a third of the page, and a blanket
`.body > div{flex-direction:column}` rule from 0.1.339 that stacked every spec strip
vertically — which alone made the cover 1301px tall inside a 720px page.


**Second pass, same release.** The four wide diagrams were redrawn rather than
rescaled, per hard rule 3. Nodes went from 46px strips to 112px cards carrying the
detail that earns the space: the S0–S4 chain gained the three ledgers with their
real status and a feedback band with a return path; the origin chain gained the
tier scale and the watershed as a decision; the funnel gained its below-threshold
branch and the two exempt classes; the evals ladder gained what each layer tests,
what it needs, and its status. Captions were compressed to a reading plus a source.

**Every page now fits 1280×720**, the primary geometry. Eight did not, and the
causes were a flex chain missing `min-height:0` at three levels, so a figure's
intrinsic height beat its cell, and an absolutely-sized cover mark. Twelve
stroke-only `<path>` polylines in the new figures had no `fill:none` and rendered
as solid black wedges — visible on the contact sheet, invisible to every metric.


**Third pass · palette, lists, captions, legends.** Four reader items.

*Colour.* The light canvas is **pure white (#FFFFFF)**, not the warm cream the
field has settled on, and the dark canvas is **Apple space grey (#1D1D1F)**. The
state palette grew from two colours to four, each with one fixed meaning and each
measured as text on its own canvas: `--amber` (#A86407 / #E0A73E) for partial, in
progress, awaiting an input; `--brass` (#7A6C52 / #C3B393) for reference and
archival. Before this, "partial" and "not built" both rendered as dashed grey, so
a deck could not say the one thing it most needed to say about itself.

*Lists are back.* "Bullet pileups are banned" had been read as "lists are banned",
and a 27-page deck shipped with **zero** `ul` or `ol` — M10 could not even be
computed. The rule now separates the pileup from the list and says what each form
is for: ordered for a sequence performed in order, bulleted for conditions that
must all hold, dashed for alternatives.

*Figure number and name go below the figure, and that does not change.* Two split
pages had moved the caption into the side column, which detached the number from
the thing it numbers.

*The legend goes where the figure wants it.* "Top right, above the plot" was
applied to every figure regardless of shape, at a size that competed with the
figure title. It is now a key in the narrative voice at caption weight, positioned
by the figure's own layout.

`inspect_layout.py` gained per-cell fill and now measures centerpiece scale against
the cell the centerpiece lives in rather than the whole page — measuring against
the page made every split look half empty when both its columns were full. Its ink
selector had also omitted lists and spec strips, so a full column of ordered steps
reported as 10% ink.


**Fourth pass · portrait, and the two thinnest pages.**

*A4 portrait is now a composition.* The width breakpoint that collapsed every
horizontal layout was the landscape design giving up; portrait now has its own
rules keyed to aspect ratio, with tighter margins, a narrower measure, and
asymmetric splits becoming a centerpiece over a band rather than two gutters.
Two-column layouts keep their columns, because 682px of content carries them.

*Figures are drawn twice.* A 2.39:1 chain in a 0.79:1 cell fills a third of it and
no CSS fixes that, so the four wide diagrams gained portrait compositions: the
same content as vertical chains. Measured, the three that had no portrait variant
sat at 71 to 73 percent empty band; with one they sit at 1.5. Aspect now matches
the cell in both geometries, 0.76:1 in portrait and 2.39:1 in landscape.

*The two thinnest pages were recomposed, not padded.* A two-row table cannot fill
a page and, worse, it hides that its two rows are opposites — the mutual-exclusion
page is now two facing cards, one per product family, each carrying its 232 status,
its country-layer status and the dimension that owns it. The filing-timeline page
moved its table to full width with the two caveats as a band beneath.

`inspect_layout.py` gained two fixes found by using it: it now measures the
*visible* figure, because a page carrying both a landscape and a portrait drawing
was being reported on the hidden one, and its ink selector had omitted the card
and definition-list elements, so a full column read as 2 percent.


**Fifth pass · page-height conformance, and the last thin pages.** The reader
noticed two pages were simply longer than their neighbours in portrait. They were:
**p18 ran 94px and p22 116px past A4**, and no existing measurement could see it,
because fill, aspect and centerpiece scale are all measured *within* a page. That
is now **D11**, reported per geometry and the first thing to read. The causes were
a callout pasted into both cells of a split and orphan one-paragraph cells left
behind by an earlier re-lay — content defects that no content metric catches.

All 27 pages now render at exactly 720px at 16:9 and exactly 1123px at A4, in both
palettes. The four-tile stat band became a grid that owns its cell and goes 2x2 in
portrait, taking two pages from 37% fill to 100%, and the trade map lost a fixed
620px cap it had been given to stop it overflowing a page it no longer overflows.


**Sixth pass · the last thin page.** p17 argued that the public record exists on
filing day while the industry announcement waits for approval, and it argued it
with a three-row table. A table cannot carry a duration. The page is now a split
with **Figure 3, a timeline**, drawn for both geometries: three accent nodes on
filing day, a dashed run of weeks or months, and a muted node where everyone
without the docket starts. Its type is set larger than the default figure scale,
because a figure carrying half a page's argument should not read as secondary to
the table beside it. No content page in the deck now sits below 45% cell fill in
either geometry.


**Seventh pass · the glossary, and H5 off 3.** Business readability had sat at 3
for four rounds because layout and colour work cannot touch it: a sales reader
meets HTS, 301, 232, GN11, RVC, HS2012, USMCA's four names and two unrelated L
numberings, and the deck offered nothing to resolve them. Twelve terms now sit at
page 7, **before the pillar pages that first use the vocabulary** rather than in
an appendix nobody reaches, and the last entry is the two-L trap the source
document calls the easiest misreading in the engagement. Four terms a reader can
infer from context were cut so the twelve that actually block a reading stand
clearly. The deck is 28 pages, still exactly one page each in both geometries, and
the usage-tier citations are now generated from page ids so they cannot drift when
a page is inserted.

The cover and closing are recomposed: the globe is part of the composition rather
than absolutely-positioned decoration mostly off-page. The remaining page-by-page
design work is open and tracked.

## 0.1.339 — 2026-08-07

Reader review of five annotated pages, all about layout. One measurement explains
most of it: **the deck contained exactly one layout, used on 25 consecutive
pages.** `.body` and `.body.top` differed only in `justify-content`, and there
were zero grid rules in the file. Every page was eyebrow, title, one block,
footer. That is a template rather than a design language, and it is why the pages
read flat and left roughly 40% of every text page empty.

**Fifteen layouts now ship**, in `tokens/lumi-layouts.css`. Vertical: `stack`,
`hero-band` (dominant block over a thin strip), `band-hero` (its inverse),
`thirds-v`. Horizontal: `split`, `split-wide` at 38/62, `split-narrow` at 62/38,
`columns-2`, `columns-3`, `columns-4`. Composite: `rail`, `quad`,
`sidebar-notes`, `full-bleed`, `diagonal-flow`.
`design-rules.md` §3 gains a content-to-layout selection table in the same shape
as §4's chart form-selection, because a vocabulary without a rule for choosing
just moves the arbitrariness one level up. This is a third token file, so version
lockstep now covers five stamps rather than four.

**The gap above the footer was mechanical.** `.fig svg{width:100%;height:auto}`
gave every figure its intrinsic aspect and no way to grow, so a 3:1 diagram in a
tall page left the difference under the footer. The centerpiece row is now `1fr`
and the figure fills it. **D7** puts a floor under it at 82% of available height,
and a page that still cannot fill has the wrong layout, which the selection table
is there to fix.

**A rule that had no floor was simply not followed.** §3 has required "one to
three sentences of support" since 0.1.336, and 10 of 25 pages had none — every
figure page plus four table pages. It is now unconditional and checked by **D8**.
Third release running that a prescribed value without a floor produced a visible
defect, which is why `CLAUDE.md` §6 exists.

**Icons extend past the eyebrow.** Labelled nodes inside figures and table
row-head groups carry their semantic icon, minimum 14px effective, honouring the
reserved bindings. **D9** caps any single layout at 40% of a deck's pages and
requires at least five distinct layouts in a deck of fifteen or more, so 25
identical pages cannot recur. **D10** reports label icon coverage.

On tilted layouts, asked for at 15, 30 and 45 degrees: **implied diagonal only**.
`diagonal-flow` gets its movement from stepped offsets and an angled accent rule
behind the blocks. Rotating body text and tables breaks printing, copy and paste
and screen reading, and a document about tariff law cannot pay that for a
flourish. On filling the text measure to the full column width, also asked for:
the cap stays at 88ch. An 1180px column at 14.5px holds about 115 characters
against a comfortable measure of 45 to 75, so filling the line would read worse.
The page was unbalanced because the right half was empty, and a second column is
what fixes that.

## 0.1.338 — 2026-08-07

Reader review of a sales-enablement deck: seven defects, and measurement said
three of them were the skill's fault rather than the deliverable's. An author
following `design-rules.md` literally would reproduce them every time.

Three failure classes sit behind the seven, and all three are now maintenance
rules in `CLAUDE.md` §4–6.

**The ladder was unreadable below its second step, and one alpha list served two
canvases.** Measured against their own backgrounds, the lower steps ran 2.91 /
1.81 / 1.32 / 1.16 on light and 4.08 / 1.99 / 1.36 / 1.16 on dark. The deck put
its eyebrows, captions, source lines, page numbers, table headers and every 9px
SVG label on those steps, which is the whole of a document's connective tissue,
and the reader's first note was that both canvases were exhausting to read. The
ladder is now two ladders with names that carry the rule: `--tx1..--tx4` for text,
every step clearing 4.5:1 against both `--bg` and `--card-bg`, and `--ln1..--ln3`
for rules, borders and fills, never text. Each palette carries its own alphas.
`--on-acc` became palette-dependent after measuring cold white on the lifted dark
accent at 2.65; until now one value claimed to serve both and white labels inside
accent bars shipped unreadable. `check_repo.py` recomputes every step and refuses
a ladder below the floor — the guard that used to enforce the shared alpha list
now enforces legibility instead.

**Two assets the rules required and the package never shipped.** §5 has demanded
a semantic icon library since 1.2 and shipped none, so the deck contained zero
icons; the eight icons now live in `assets/icons/` with `scripts/embed_icons.py`.
The cover rule banned imagery because the skill had no photo library, applying the
ban to every kind of image when photography was the actual risk; `assets/vectors/`
now ships an orthographic globe and a flat trade map, generated from lat/lon by
`scripts/build_geography.py`, and a cover may carry exactly one vector mark. Both
are the defect 0.1.337 fixed for the display face, repeated one directory over.
`.gitignore`'s blanket `*.svg` would have dropped both silently and now carries
the exceptions.

**Prescribed values with no floor.** The type scale had no minimum and its two
copies disagreed (tokens 11 / 10.5 / 9.5 against prose 14 / 10–11 / 11, tokens
winning, so 9.5px source lines shipped); there is now an 11px floor and the scale
is 13 / 11.5 / 10.5. The three callout tiers had no budget and a deck put 18
tier-one callouts on 14 of 27 pages, so the hierarchy degraded back into the flat
page it was introduced to fix; tier one is now capped at one per page and a third
of a deck's pages. The figure vocabulary had no consistency requirement and one
figure carried three shape kinds, six dashed states and nine arrows while four
others were rectangles and text; figures must now hold one level across a
document, and a grid of rectangles containing sentences is a table. Footers carry
`N / total`.

**A ceiling read as a target, for the third time.** "Titles budget two lines"
produced titles engineered to two lines: the author capped the container at 48ch
and all 24 content titles broke near the middle. One line is now the goal, two the
ceiling, and narrowing a title container to manufacture a break is banned outright.
0.1.332 and 0.1.336 record the same shape, which is why it is now a maintenance rule.

**`scripts/check_design.py` (D1–D6)** makes the design half of the skill checkable
the way M1–M11 made the prose half: contrast, type floor, callout budget, palette
purity, figure parity (reported, not graded — the judgement is not automatable),
footer completeness. Run against the 0.1.337 deck it reports 32 contrast failures,
17 sub-floor type sizes, four pages over budget on 51.9% of pages, and two footer
gaps, which is the reader's list in numbers. `eval-rubric.md` also now requires a
self-score to carry its reasons; a bare number gives a reviewer nothing to diverge
from.

**Second reader pass, before this release shipped.** Two more defects, and both
say the same thing about how it was verified.

*The icon set was too small to say anything.* Eight hand-drawn icons across
twenty-five pages meant `gauge` did five jobs and the reader called the match to
content poor. Fixed by vendoring Lucide (2007 icons, ISC, `assets/icons/lucide/`,
searchable through its `tags.json`) and keeping LUMI's contribution where it
belongs: the reserved bindings in `scripts/embed_icons.py` that pin one icon per
recurring meaning. `embed_icons.py` now emits a **subset** sprite — the deck
embeds 25 icons in 7.7 KB rather than 0.9 MB of library. Breadth and consistency
are separate problems and a house set of eight solved neither.

*A figure shipped clipped.* The evals-ladder band was extended to y=212 inside a
viewBox 208 tall, so its bottom edge was cut and it collided with the caption.
`check_design.py` said all-clear because it reads declared CSS and cannot see
rendered geometry. Three browser checks are now in `design-rules.md` §7 — every
drawn element inside its viewBox, every label inside its shape tested at the
corners rather than the midline, and both re-run after any type-size change,
which had moved seven labels out of their boxes at once. Two of those three
probes passed clean on the visibly broken document before they were corrected,
hence the rule that a probe which has never failed is not a probe.

Also from this pass: a decision diamond had been used for a state, to satisfy the
new figure-parity rule. Parity means building every figure to the same level, not
using the same shapes regardless of meaning; the shape vocabulary still binds.

Two maintenance rules in `CLAUDE.md` (§7, §8) and one scoring rule in
`eval-rubric.md` (§3b): a validation artifact is never a source of conventions,
metrics passing is not a verified document, and a dimension where the reader found
a defect the author claimed to have verified cannot be self-scored above 3 in the
round that fixes it.

Deferred to a later round, recorded so it is not lost: a `check_version.py` that
tells a user of Claude Code, Codex or Gemini that their installed copy is behind
upstream. The immediate mitigation is to install the skill as a symlink to a git
checkout, which makes drift structurally impossible — the copy this round was
built against had been stranded at 0.1.334 while the repo reached 0.1.337.

## 0.1.337 — 2026-08-07

Two operational gaps, both found by asking why a step kept costing time.

**The display face now ships with the skill.** `design-rules.md` has required
D-DIN to be embedded since 1.2, and 1.2 itself shipped with the face declared but
not vendored, so it rendered nothing. The rule was right and the package could not
satisfy it: every deliverable's author had to find the font again. The two woff2
files (43 KB together) now live in `assets/fonts/` with their OFL text, and
`scripts/embed_font.py` prints the ready `@font-face` block or verifies the files
with `--check`. Confirmed the vendored files produce base64 byte-identical to the
already-shipped deck, so nothing about existing deliverables changes. CI checks
the sizes, because a silently swapped face would alter the metrics of every
document that embeds it. Note that `.gitignore` blocks font formats as
deliverable output and now carries an explicit exception — the face is part of the
design language, not a render.

**Waiting on CI is now bounded and outage-aware.** During the 2026-08-06 Actions
incident, open-ended polling consumed most of a working session and merged
nothing: runs queued for six minutes, were cancelled, were re-run, queued again.
`scripts/ci_wait.sh` asks the status page *before* waiting and short-circuits when
Actions is degraded, otherwise checking three times over about four minutes and
then stopping. The protocol behind it is recorded in `CLAUDE.md`: correctness is
answered locally by `check_repo.py` in seconds, CI only unlocks the merge button,
a cancelled run is a symptom rather than a verdict, and re-running into a declared
incident adds to the load causing it.

## 0.1.336 — 2026-08-07

Internal review: sales and marketing deliverables still read as AI-written. The
`humanizer` skill (github.com/blader/humanizer, MIT) was evaluated as a candidate
fix and its rules adapted rather than the skill adopted — LUMI keeps one source of
truth and no runtime dependency. See `NOTICE` for attribution and scope.

The evaluation found three causes, and humanizer only addresses the first:

1. **Coverage was lexical, not structural.** The `[en-output]` ban list was a
   five-item seed while English had been the default output language since 0.1.333,
   and the "delete filler phrases" move shipped without a list of filler phrases.
2. **The de-AI-flavor pass was an orphan.** It is the repo's only real
   anti-AI-flavor machinery and no workflow step, checklist, gate, or metric
   invoked it; it was absent from `prompts/lumi-style-core.md` entirely, so Kimi
   and DeepSeek users got none of it. The repo already knew the lesson — "a pass
   in the pipeline beats good intentions" — and had applied it only to punctuation.
3. **The mandated forms were themselves the tells.** A deliverable could satisfy
   every rule, score clean on all eight metrics, and still read as machine-written,
   because compliance is what made it read that way.

Changes:

- **[en-output] ban list grown from 5 entries to 8 grouped classes** — significance
  inflation, promotional register, AI high-frequency vocabulary, filler with its
  fixes, authority tropes, signposting, fake-candid openers, closing filler.
- **De-AI-flavor pass is now mandatory and gated**, with seven structural moves
  added (em/en dash ban for en sales/marketing, rule-of-three, list-shape variety,
  inline-header bullets, manufactured punchlines and aphorism formulas, boldface
  inflation, synonym cycling) and a two-pass audit: ask the draft what makes it
  obviously AI-generated, then fix what you named, and confirm no fact was added.
- **New section 6b, de-translationese** — sales and marketing material is now
  authored in English with Chinese translated from it, which imports a second
  failure mode. Precedent: 0.1.329 translated the Chinese rule "not X, but Y" into
  "Not X. Y.", models rendered it back into Chinese, and the round trip amplified
  until readers called the decks AI-flavored.
- **Conflicts with LUMI house style resolved in humanizer's favor**: negation-first
  openings retired as a mandated signature and stripped of their de-flavor
  exemption; the three canned responsibility frames reduced to a disclosure
  requirement phrased in the sentence's own words; the "short sentences" mandate
  replaced by a variance requirement; the accent-word bold made optional.
- **Structural loosening** — the colon title is the reference form, not the
  required one (capped at 60% of titles by M11); sibling-page parallelism only
  where it aids comparison; one to three support sentences of visibly differing
  length per page; the page arc is a default order rather than "never reorder";
  the stock metaphor and the imperative closing line are no longer mandated.
- **M8 is now two-tailed** (overlong share plus a sentence-length variance floor)
  and never waived for decks: it used to count only long sentences, so uniformly
  clipped prose — the dominant modern AI tell, and what the voice rule itself
  mandated — scored a perfect zero. **M9-M11 added**: em dashes, triad rate,
  title-shape uniformity.
- **`scripts/check_prose.py` added.** M1-M8 were called "scriptable" for six
  versions with no script in the repo. This measures M4 and M8-M11 on a real
  deliverable, and reports a file it could not parse as *unmeasurable* rather
  than clean — a linter that says "pass" when it read nothing is worse than none.
- `scripts/emergency_merge.sh` added: a documented, self-restoring path to merge
  when GitHub Actions cannot run the required check. `.gitignore` now also blocks
  deliverable exports and renders — this repo holds the skill, never its output.
- **CI now covers `scripts/`** (`py_compile` plus `bash -n`). It had none, so a
  syntax error would have shipped silently — including into the emergency path
  that runs precisely when CI is unavailable.
- **Fifth guard: ban-list parity.** `check_prose.py`'s phrase list is a second
  copy of §2 and was held to it only by a comment saying "change both together".
  `check_repo.py` now parses §2 and the script's declarations (by AST, so the
  guard never executes the other script) and fails when they disagree in either
  direction. Phrases that cannot be matched mechanically — `rich (figurative)`,
  `key (adjective)`, "adjective stacks in place of numbers" — must now be listed
  in `NOT_MECHANIZED` with a reason, which turns the gap between what the rules
  ban and what the machine can enforce from invisible into documented.

Review round on this release, recorded because the findings were real:

- The emergency merge script executed code supplied by the pull request. Copying
  a trusted `check_repo.py` over the PR's copy was not enough — the script's own
  directory is `sys.path[0]`, so a planted `scripts/json.py` hijacks an import
  and runs. Reproduced, then fixed with `PYTHONSAFEPATH=1` (Python 3.11+ now
  required) plus fork refusal and a merge-ref parent check.
- Its restore path could leave `main` unprotected while exiting 0, and a signal
  handler that returned instead of exiting let a killed merge report success.
  Distinct exit codes now separate "refused", "check failed", "could not run the
  checker", "merge failed", and "protection still off".
- `check_prose.py` matched multi-word entries as unanchored substrings and single
  words with word boundaries — exactly backwards. It flagged "deserves as much"
  and a finance "leverage ratio" while missing "leveraging" and "fostering", the
  actual tells. Every entry is now an explicit anchored pattern with its
  inflections, and ordinary business words are qualified rather than banned.
- Empty, non-UTF-8, and unparseable files reported "all metrics pass"; `--json`
  never evaluated a threshold and always exited 0; HTML markup merged into
  27-word pseudo-sentences that inflated the rhythm metric. All fixed and each
  verified against the failing case.

## 0.1.335 — 2026-08-07

Reader review of two shipped sales decks (zh + en, V0.1.333) against their own
V4.1 predecessor: "page titles suddenly became very short and AI-flavored,
overusing the it-is-X-not-Y contrast — this violates the PwC title principle the
skill was founded on." Measured: title length fell from a median of ~29 CJK
characters to ~8; display type rose 29.8pt → 37.4pt; every evidence figure
(18×, 4,557, 194, 29,845) vanished from the title line.

Root cause: 0.1.332 answered a review complaint about *visual* divergence from
spacex.com by writing a *writing* rule — "a giant short headline (3–6 words)" —
into design-rules §3, without reconciling it against the PwC title contract that
already existed in storyline-templates. The word ceiling then collided with the
still-standing requirement that a title be a complete assertion carrying the
takeaway, and with the negation-first signature's explicit de-flavor exemption;
in ~6 CJK characters the only form that satisfies all three is a bare antithesis.

- **The word ceiling is removed.** design-rules §3 now defers to the title
  contract; headline length follows the fact, bounded only by the two-line budget.
- **Title contract promoted to shared discipline** (was scoped to the consulting
  template, so sales decks had no title rule at all): "Topic: assertive subtitle",
  naming a subject and carrying a verifiable fact.
- **Information floor added**: a bare contrast, a slogan, or a section label is
  not a title. Contrast is a lead-in that must keep the evidence that earns it.
- **Two-line guard rewritten**: display titles are a size *range*; a long title
  takes the lower end before any word is cut. The old "shorten the title, never
  shrink the type" left cutting words as the only legal move once titles went
  giant, and the evidence went first.
- **Negation-first scoped** to the cover and hook, once per document; it is not a
  page-title form.
- **M1 is never waived for decks.** It had been marked "distorted for slides —
  advisory", which removed the only metric that measures this exact failure; the
  regression ran three versions unmeasured.

## 0.1.334 — 2026-08-06

Reader review of the anchor document (five annotated screenshots):

- Long-document callout hierarchy: three tiers (tinted+bordered key conclusion /
  left-rule guidance / muted note) — one uniform left-rule flattens the page.
- Charts: legend at the top right above the plot; two-part caption anatomy
  ("Figure N · Name" centered bold, description left-aligned at figure width).
- Flow-diagram shape vocabulary: parallelogram=I/O, rectangle=process,
  diamond=decision, stadium=terminal, dashed=not built — shapes carry semantics.
- Figure vocabulary ⊆ body vocabulary: body renames must sweep figure labels.
- Deliverables state results, not process: revision stories live in the ledger.
- Version lockstep refined: a user-assigned document-edition sequence (v1.01)
  owns filename+masthead; the colophon still records the producing skill version.

## 0.1.333 — 2026-08-06

Reviewer-driven round (five inputs from deck review):

- **Light-first**: the default canvas is near-white with the ink ladder; dark is
  applied only on explicit request via one `body.dark` override block. Both
  palettes share one token structure; literal colors in components or inline
  SVG are defects. Full dual-palette token set in `tokens/` (lumi-theme.css
  rewritten to v0.1.333; design-tokens.json restructured as palette.light /
  palette.dark).
- **American English by default**: when the user does not specify a language,
  output is American English (spelling, idiom, double quotes, serial comma);
  writing-rules §0 rewritten.
- **Icon-alignment guard** (from a reported alignment bug): an icon on a text
  line lives in a flex container with align-items:center — never a bare inline
  SVG nudged with vertical-align; icon ≈ 1.4× the accompanying text size.
- **Version lockstep**: a deliverable's version number is the lumi-style version
  that produced it; carried on the cover meta strip and closing colophon.
- **Cover and closing templates**: every deck opens with a typographic cover
  (wordmark / title / meta strip) and ends with a closing page (closing
  statement / recap / contact placeholder slots `[TO FILL]` — inventing contact
  details is inventing a fact / colophon). Added to storyline-templates.

## 0.1.332 — 2026-08-06

Direction change, reviewer-driven: "the output diverged from spacex.com — why?"
The 1.x fusion ("skeleton only, keep rounded type and light canvas") kept too
much consulting-deck idiom, and the one adopted SpaceX element (D-DIN in the
data voice) never shipped because the font was declared but not vendored.

- design-rules: decks are **dark-first** (near-black canvas, cold-white ink
  ladder); light canvas stays for long documents.
- design-rules: **D-DIN takes over** as the single Latin face; ALL-CAPS
  display titles at weight 400; rounded faces retired from decks; vendor and
  embed the font — a declared-but-unshipped face renders nothing.
- design-rules: one-statement-per-screen sharpened (giant short headline, one
  support sentence, one centerpiece, thin footer); hairline rows over card
  boxes on dark canvases.
- Accent green lifts to a dark-canvas form (#7C9F63); red text on black uses a
  lifted form while fills keep the seal red.

## 0.1.331 — 2026-08-06

- design-rules: added three field-tested guards from a reader-reported bug round —
  two-line title budget (shorten, never shrink); icon size independent of
  container scaling (blanket `svg{width:100%}` rules must exclude icons; an
  accidentally-stretched icon is not a design choice); in-row card alignment
  constraints (equalized title heights, stat numbers stacked above labels).
- design-rules: new "Verification matrix" section — language axis × viewport axis
  (design / print / short-laptop); footer rule and page number must be visible at
  every matrix point; height-based media queries as the mechanism. Supersedes the
  standalone localization guard (merged in).

## 0.1.330 — 2026-08-06

- Added the localization layout guard to design-rules: translated text runs
  30–50% longer/shorter — re-inspect every fixed-width container page by page
  after any localization pass. (From the English-deck audit: seven layout defects
  found — a wrapped stat band, ragged stat labels, and three SVG text overflows.)

## 0.1.329 — 2026-08-06

- **Repository language: English only — declared a red line.** LUMI serves a
  global audience; all rule prose, entry points, adapters, tokens, and this
  changelog are now English. Chinese strings remain only as rule data for
  Chinese-language output (banned phrases, punctuation patterns, collocation
  examples).
- Rules generalized to be output-language-aware: language-agnostic core
  (facts / voice / structure / charts) + a marked [zh-output] module; an
  [en-output] banned-phrase seed added.
- New field-tested layout guard in design-rules: right-anchored labels on
  full-width bars must anchor inside the fill (white-on-white invisibility bug,
  caught in per-page inspection).

## 0.1.328 — 2026-08-06

Initial release. Rules distilled from six rounds of real delivery polishing and a
first round of reader review on a consulting engagement's deliverables:

- Terminology red lines: no coined Chinese; direct English for concepts without
  an established Chinese term; substring-collision exemptions;
- Banned AI-tell phrases (with the "sales enablement" fixed-collocation lesson);
- Number discipline: sourcing, illustrative labels, repo-wide retraction with
  retirement notes for unreliable citations;
- The "value & future" sales storyline (boundaries converge to one trust page) —
  from a reader review scoring H5=2;
- "So-what is a writing discipline, not a page element" — from a reader review
  scoring H1=1;
- Plain-language scoring anchors ("anchors must be written in the reviewer's
  language") — from a reader review scoring H2=1;
- Five chart iron rules and form selection (partly adapted from
  enterprise-ai-skills, localized);
- Visual tokens v2: space-gray canvas + natural green single accent + China red
  warnings; layout skeleton informed by SpaceX/Tesla research (transparency
  ladder, dual-voice typography, cold-white dark canvas).
