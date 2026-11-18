---
name: html-explainer
description: Explain something to Lawrence as a single self-contained HTML page built around figures - charts, step-through sequence diagrams, system diagrams, timelines and clickable visuals - written for a staff data scientist who knows ML and statistics cold and wants the mechanism, the numbers and the caveats. Use whenever the user asks for an explainer, an "effective-html", an explanatory HTML artifact or HTML page about a topic, a diagram or visualization "to help me understand", or a visual summary of research, a paper, a model, a training method, a system, a piece of work just done, or a hard passage or history, and when they say "explain this visually", "show me how this works", "create a diagram explaining this" or "give me this explanation as an html file". Prefer this skill to a prose answer whenever they ask to understand something and a picture would carry it. Not for building an app that will be deployed, for slide decks, or for converting existing content to HTML.
---

<!-- Adapted from plannotator/effective-html (MIT), https://github.com/plannotator/effective-html:
     its build contract and "big pictures, little words" idea, narrowed to one reader. -->

# HTML explainer

One page that makes a subject click for one particular reader. That reader is Lawrence: a
staff data scientist and AI engineer who thinks in plots, reads Python and SQL fluently, and
would rather see a mechanism drawn than described. He has asked for pages like this dozens
of times, about model training, research papers, industry practice, home networking,
history and Scripture, and the ones that work are the ones where the figures do the
explaining and the prose only says what a figure can't.

So the rule of thumb for every decision below: **show it, put a number on it, and let him
poke at it.**

## Who you are writing for

Assume without explaining: probability and statistics, the ML training loop, loss
functions, embeddings, transformers at the block-diagram level, evaluation metrics,
experiment design, Python, NumPy, SQL, git, coding agents. Explaining these wastes his
attention and reads as talking down.

Explain from first principles: whatever is outside that, which is often the actual subject.
Networking, cryptography, hardware, tax law, theology, history, biology. Here he is a
smart newcomer, and a term used before it is defined loses him.

Where a subject straddles both, bridge from what he knows: an unfamiliar system mapped
onto a pipeline he has built, a new training method shown as a diff against plain
fine-tuning, a quantity given next to one he has a feel for.

What "staff level" changes: he wants the mechanism and not only the result, baselines next
to every headline number, distributions and intervals rather than bare means, the sample
size, what was held fixed, and where the evidence is thin. A page that only repeats a
source's claims is a summary. He is asking for understanding, which includes knowing how
much to trust it.

If the page is for someone else (his wife, a church group, his team), he will say so. Then
the audience changes and everything in this section is recalibrated to them, but the
visual-first approach stays.

## Start from the questions, not the outline

Before writing any HTML, settle these (in your own reasoning; no notes file is needed):

1. **The one question** the page answers, and the one-sentence answer.
2. **Three to six sub-questions** a sharp reader would ask next, in the order he would ask
   them. Each becomes a section.
3. **For each sub-question, the figure that answers it**, chosen by the kind of question.
   Read [`references/figures.md`](references/figures.md) for the mapping and for what makes
   each kind of figure good. If you can't name a figure for a section, the section is
   probably prose padding; merge or cut it.
4. **Where interaction earns its place** (see below).
5. **What you actually know versus what you are inferring**, so the page can say so.

If the subject needs facts you don't have (a paper, a product, current numbers), get them
first: read the source he gave, search, or read the code. Don't draw a confident diagram of
something you are guessing at.

## The shape of the page

Start from [`assets/template.html`](assets/template.html). Copy the file with `cp` to the
output path and edit the copy in place: replace the contents of `<main>` and the demo block
at the end of the script, and leave the styles and helpers as they are. Don't retype the
helpers into a new file; they are dense and a transcription slip breaks every figure. It gives every explainer the same reading
experience (he reads many of these, so a familiar frame is a feature), follows light and
dark mode, and has no external dependencies.

In order:

1. **Title as the question, then the answer in one sentence.** No preamble.
2. **Bottom line**: three bullets at most. The claim with its number, the mechanism in a
   clause, the main caveat. Someone who stops here should still leave correct.
3. **The whole picture**: one diagram of the entire thing before any part is examined. The
   later sections zoom into pieces of this figure, so reuse its colours and names.
4. **Sections**, each built the same way:
   - an `h2` that states the finding ("Rank 1 scored the same as rank 64"), not the topic
     ("Effect of rank")
   - the figure, immediately
   - a "Read it as" caption that says what to notice
   - two or three sentences for what the figure can't show: why, what was held constant,
     what is surprising
   - optionally a closed `<details>` holding the math, code or derivation, so depth is one
     click away without being in the way
5. **A worked example with real numbers.** Push one small concrete case through the whole
   mechanism so that every symbol has a value: an actual tensor shape, an actual row, an
   actual dollar amount. This is frequently the section that produces the "oh".
6. **What's uncertain**: what wasn't measured, what the source only asserts, what you
   inferred, and the first check you would run. Keep it specific; a generic disclaimer is
   noise.
7. **Sources**, linked, each with a few words on what it was used for.

Use real `h2` and `h3` headings throughout and keep the short section nav at the top once
there are more than four sections. He scans by heading and has asked for them when they
were missing.

Keep prose short. As a guide, a section's running paragraphs (not counting captions,
tables, the details block or the uncertainty list) stay under about eighty words; past
that it usually needs a second figure instead. The sub-question sections are in addition
to the fixed ones, so a page with four sub-questions has around eight headings, which is
fine. Past ten, merge.

When the explanation depends on details of his situation that you don't have (how many
labels, how much data, which hardware), pick a stated placeholder, make it a control if it
changes the picture, and list it under what's uncertain. Don't stall on it and don't hide
it.

## Figures

The template includes three helpers; read the comment above each in the file for its API.

- **`Fig`** draws charts: lines, dots, bars, interval bands, error bars, shaded spans,
  reference lines, annotations, linear, log and categorical axes, hover and keyboard
  tooltips, and a data table under the chart. Use it for anything quantitative so axes, ticks and theming are right every time.
- **`Seq`** draws a sequence diagram the reader steps through: actors across the top,
  messages in time order, each one clickable with its own explanation. He likes these.
  Reach for one whenever the subject is "who sends what to whom, in what order": a request
  path, a training step, a protocol handshake, an agent loop with tool calls, a rollover of
  money between accounts, the movements in a narrative.
- **`data-explain`** makes any element click-to-explore: put the explanation in the
  attribute, point `data-panel` at a panel, and clicking or pressing Enter shows it. Use it
  on the boxes of a hand-drawn SVG diagram so the overview stays clean and the detail is on
  demand.

Diagrams of structure (architectures, pipelines, topologies, family trees) are drawn by
hand as inline SVG using the template's `d-*` classes. Give different kinds of thing
different shapes and colours and say what they mean; a wall of identical rounded boxes
joined by arrows tells the reader nothing. Put tensor shapes, units or types on the
elements where they apply.

Rules that matter more than any helper:

- **Every number on the page is real.** From the source, from the code, or computed by you
  and shown. If a figure needs illustrative values to show a shape, label the figure
  "illustrative" in its subtitle. Never let made-up numbers pass as data.
- **Say what kind of claim each key number is** with the template's chips: measured,
  reported (the source says so), computed (exact arithmetic you did from stated inputs),
  estimate (yours), inference.
- **The title of a chart says what it shows; the caption says what to conclude.** Label
  units, ranges and sources. Say when an axis is log or doesn't start at zero.
- **Direct-label lines and bars** (`label` on lines, `value: true` on bars) instead of
  using a legend the eye has to travel to.
- **Colour means one thing per page.** If orange is "trained" in the overview, it is
  "trained" everywhere. Don't rely on colour alone; pair it with shape, label or position.
  Selection and focus are drawn in the ink colour by the template, so they never read as a
  category. The evidence chips and links keep their own fixed colours; avoid reusing those
  for a data series that sits next to them.
- **Annotate the point of the chart on the chart**: the knee, the crossover, the outlier.

If a dedicated data-visualization skill is available in the session, read it for chart
mechanics and keep this skill's structure and reader.

## Interaction

Add it where it lets him answer his own follow-up question, and leave it out where it is
only motion. The kinds that have earned their keep:

- **Stepping through a sequence**, building the picture one message at a time (`Seq`).
- **Clicking a part to see what it is**, on diagrams with more detail than fits as labels.
- **A slider on the one parameter that drives the behaviour**: rank, learning rate,
  interest rate, sample size. Recompute the figure live and show the current value. One or
  two controls, with the default set to the case the text discusses.
- **Toggling between two or three views of the same thing**: before and after, with and
  without, linear and log.
- **Hover or focus for exact values** on charts, with the table available for the rest.

Everything essential must be visible without interacting: the default state of the page is
a complete explanation, and the interaction adds depth. Every control works from the
keyboard, shows its current state, and can be reset (a Reset button that restores the
defaults is enough). A control redraws a chart by rebuilding it: see the "Live update" note
in the template's `Fig` comment. For a parameter with a few meaningful values (rank 1, 2,
4, 8), drive a slider over the index into that list, not over the raw number. The template's
demo chart has a working slider and Reset to copy from. Motion that only decorates is left
out, and `prefers-reduced-motion` is respected.

## Build rules

- One `.html` file with its CSS and JavaScript inline. It opens from disk with no network
  and no build step, so it can be downloaded, emailed or dropped on a server. No CDN
  scripts, no web fonts, no external images unless he supplies them.
- Semantic HTML, readable at phone width and on a wide monitor, nothing overflowing the
  page sideways (put wide tables in the template's `.scroll` container).
- Equations: plain Unicode in running text (`ΔW = B·A`), and a code block in NumPy-style
  notation with shapes in comments for anything longer. He reads that faster than
  typeset math, and it needs no library.
- No placeholder text, decorative statistics or controls that do nothing. Delete every
  part of the template the page doesn't use, including the demo figures.

## Deliver it as a file he can open

- Write it into the current workspace under a clear name, `explainers/<topic-slug>.html`
  unless the repo has an obvious home for such pages or he named a location. A real file on
  disk is the deliverable; he has had to ask for "the html I can download" when he was
  only given a rendered preview.
- If the session can show HTML (an artifact or preview pane), show it there as well, and
  still give the file path.
- Publish it anywhere (his html-server, a repo, a share link) only when asked.

## Check it before handing it over

Open the file in a browser and look at it, at a wide and a narrow width. Most defects in
these pages are visual (a label on top of another, a line that didn't draw) and can't be
seen any other way:

- no console errors; every chart and diagram rendered
- labels don't collide, clip or run off the edge; arrows end where they should
- click every control and step through every sequence to the end and back
- it reads in both light and dark mode
- the template's demo content is gone

With no browser available, do the part that can be done and say plainly in the report that
the page was never rendered: extract the script and run `node --check` on it, confirm every
`Fig`/`Seq` target id and `data-panel` exists in the markup, and search for leftover
template text (`EXPLAINER TITLE`, `DATE`, `demo`).

Then read it once as he would, asking of each figure: "what do I now know that I didn't?"
A figure with no answer gets redrawn or removed. Finally, check each number against where
it came from.

Report in two or three lines: the path, the question it answers, the figures in it, and
anything you could not verify.
