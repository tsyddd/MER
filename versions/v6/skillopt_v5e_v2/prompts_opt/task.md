<!-- Adapted from microsoft/SkillOpt (MIT, see LICENSE-SkillOpt.txt). Prepended to every optimizer prompt of version 2. -->
## Task context (read first)

The TARGET agent classifies the emotion of the target speaker in a short video clip. It works in up to three stages and always chooses its
answer from `candidate_labels` (the answers of three earlier experts; the agent may not add labels):
- **first**: reads 8 frames + subtitle (+ audio) and gives a first answer with 1-3 located evidence items; it may name ONE specific uncertain
  point and the time window to look at again.
- **relook**: only when an uncertain point was named. Reads denser frames / the audio segment of that window and answers the point.
- **reflect**: compares the first answer with the relook result and decides KEEP or REVISE (REVISE needs new, locatable evidence).

The SKILL DOCUMENT has one section per dataset. All trajectories below come from ONE dataset (named in the request); you edit only that
dataset's section. The section has three modules, each stage reads only its own module:
- `first`  (A differentiating cues between the candidate labels + B when to name an uncertain point and how to phrase a re-look question)
- `relook` (C what to look for in the re-look frames / audio, and how to answer when nothing new is visible)
- `reflect`(D what counts as new, locatable evidence, and when to KEEP)

You (the reflection model) can WATCH the frames (and listen to the audio, when provided) of every trajectory. Use them: check whether the
target's evidence is really visible / audible, and whether the gold label is better supported than the target's answer. The gold label is
shown to you only.

## Rules for every edit (violations are dropped by a program)
- Each edit has a `"module"`: `"first"`, `"relook"` or `"reflect"`, and only changes that module of this dataset's section. Write in Chinese.
- Write GENERAL principles that help on other clips: how to tell two labels apart, which cue to check. Do NOT write: sample ids, quotes of
  subtitles or evidence, statements about a specific clip, numbers / percentages / counts, or anything about the output format or JSON fields.
- Use only label names of this dataset (they are listed in the request).
- **No default-label rules.** Never write "prefer / default to / when unsure choose label X", "X 优先", "一律判为 X", "应果断改判 X" or anything that
  pushes the answer toward one label without naming the cue that supports it. The evaluation counts every class equally, so a rule that only
  shifts answers toward a frequent label is rejected. Every rule must say which observable cue separates which labels.
- A module shown as `（空）` is empty: use `"op": "append"` for it. `target` must be text that already exists in that module.
- Keep each edit short (at most ~3 sentences). Do not weaken the rule that labels must be chosen from `candidate_labels`.
