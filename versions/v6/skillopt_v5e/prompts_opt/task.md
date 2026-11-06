<!-- Adapted from microsoft/SkillOpt (MIT, see LICENSE-SkillOpt.txt). Prepended to every optimizer prompt. -->
## Task context (read first)

The TARGET agent classifies the emotion of the target speaker in a short video clip (datasets MER2024: 6 classes; MELD: 7 classes).
It works in up to three stages and always chooses its answer from `candidate_labels`:
- **first**: reads 8 frames + subtitle (+ audio) and gives a first answer with 1-3 located evidence items; it may name ONE specific uncertain
  point and the time window to look at again.
- **relook**: only when an uncertain point was named. Reads denser frames / the audio segment of that window and answers the point.
- **reflect**: compares the first answer with the relook result and decides KEEP or REVISE (REVISE needs new, locatable evidence).

`candidate_labels` = original candidates (answers of three earlier experts, `original`) + expanded labels (`expanded`, added by a confusion
lookup: when the answer is some original candidate c, the true label is sometimes the expanded label). The target agent may not add labels itself.

One SKILL DOCUMENT with three modules is appended to the target's prompts, each stage reads only its own module:
- `first`  (A differentiating cues between the candidate labels + B when to name an uncertain point and how to phrase a re-look question)
- `relook` (C what to look for in the re-look frames / audio, and how to answer when nothing new is visible)
- `reflect`(D what counts as new, locatable evidence, and when to KEEP)

You (the reflection model) can WATCH the frames (and listen to the audio, when provided) of every trajectory below. Use them: check whether
the target's evidence is really visible / audible, and whether the gold label is better supported than the target's answer. The gold label is
shown to you only.

## Rules for every edit (violations are dropped by a program)
- Each edit has a `"module"`: `"first"`, `"relook"` or `"reflect"`, and only changes that module's text. Write the skill text in Chinese.
- Write GENERAL principles that help on other clips: how to tell labels apart, what cues to check. Do NOT write: sample ids, quotes of
  subtitles or evidence, statements about a specific clip, the gold label of a clip, numbers / percentages / counts, or anything about the
  output format or JSON fields.
- A module shown as `（空）` is empty: use `"op": "append"` for it. `target` must be text that already exists in that module.
- Keep each edit short (at most ~3 sentences). Never copy the gold label of a trajectory into a rule; describe the cue instead.
- Do not weaken the rule that labels must be chosen from `candidate_labels`.
