# Karpathy's four guidelines · id `EX-4`

*Serves: **GOAL**.*

Archived 2026-08-19 from `multica-ai/andrej-karpathy-skills` (MIT), which
derives them from Andrej Karpathy's published observations on how LLMs fail at
coding. Brought in by owner directive after a retrospective on five deck builds
in two days, every one delivered gate-green and every one returned with defects
no gate can see.

**This file is provenance, not the mechanism.** The audit that prompted it
found that `references/exemplars/` is precisely where absorbed knowledge goes to
be inert: EX-1's ten devices reach the codebase nowhere, EX-3's ten rules
survive as eleven section nouns, and `assets/frameworks.json` was validated by a
guard and read by no runtime for six releases. Archiving a fifth study and
expecting behaviour to change would be this repository's own diagnosis, repeated.
**The two guidelines that bind here are `CLAUDE.md` conventions 17 and 18**, and
they bind because they are conventions, not because they are quoted below.

## 1 · Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs. State assumptions
explicitly and ask when uncertain; present competing interpretations rather than
picking silently; say so when a simpler approach exists; stop and name what is
confusing rather than proceeding through it.

## 2 · Simplicity first

The minimum that solves the problem, nothing speculative. No unrequested
features, no abstraction for single-use code, no configurability nobody asked
for, no error handling for impossible cases. *Would a senior engineer call this
overcomplicated?*

## 3 · Surgical changes

Touch only what you must; clean up only your own mess. Don't improve adjacent
code, don't refactor what works, match the existing style, flag unrelated dead
code rather than deleting it — and remove only the orphans your own change
created. **The test: every changed line traces directly to the request.**

*This is convention 17's source, generalised from code to deliverables: a
rebuild that quietly drops content is the same defect as a refactor that
quietly drops a function.*

## 4 · Goal-driven execution

Define success criteria, then loop until verified. Turn a request into a
checkable objective ("add validation" → "write tests for invalid inputs, then
make them pass") and, for multi-step work, state the plan as step → verify
pairs. **"Strong success criteria let you loop independently. Weak criteria
require constant clarification."**

*This is convention 18's source, and it is the sentence that explains why an
owner had to ask five times: with no criterion beyond the gates, the loop
terminates at the gates.*
