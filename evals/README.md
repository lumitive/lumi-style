# evals/

`thresholds.json` is the bar a deliverable is held to, per genre, with the
evidence that set each number. `scripts/ops/eval_corpus.py` scores documents
against it.

**Why every cell carries an `evidence` level.** This package withdrew an invented
threshold once — 0.1.339's 82% page-fill floor, satisfied by stretching table
rows, its reader scoring three dimensions at 1. A table of numbers with no
provenance is that failure waiting to repeat, and only two genres have a
document on record, so most cells cannot be more than reasoned. Read the level
before trusting the number; the counts are in the file, not in prose that can
fall behind it.

**Why the corpus is identified by id.** Red line 9: this repository holds style
rules and templates, never client names, project figures or engagement facts. A
corpus entry naming a real deliverable is an engagement fact in a tracked file.
So `thresholds.json` carries `A1` and `R1`, and the paths live in

    evals/corpus.local.json     (gitignored; yours, not the package's)

shaped like:

```json
{"A1": "~/Documents/LUMI-Style/some-accepted-document.en.html",
 "R1": "~/Documents/LUMI-Style/some-rejected-document.en.html"}
```

`eval_corpus.py --corpus` reads it if present and says plainly what it could not
resolve if it is absent. Naming a file you have is not a fact about a client;
naming it *here* would be.
