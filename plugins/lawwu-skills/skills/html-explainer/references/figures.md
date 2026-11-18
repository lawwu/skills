# Choosing the figure

Pick the figure from the question the section answers. The left column is how the question
sounds; the right is what to draw and which helper in `assets/template.html` draws it.
Chart layers are methods on the object `Fig(...)` returns, written here as `.line()`.

| The reader is asking | Draw | With |
|---|---|---|
| What are the parts and how do they connect? | System or architecture diagram, shapes and colours by kind | hand SVG + `data-explain` |
| What happens, in what order, between whom? | Sequence diagram, stepped | `Seq` |
| What changes from stage to stage? | Pipeline with the data shape or state written at each stage | hand SVG |
| How did it move over time or training? | Line chart, direct-labelled, with the event annotated | `.line()` + `rule` + `note` |
| How do the options compare? | Sorted bars with the baseline marked, or a small table when exact values matter | `.bars()` + `rule` |
| How are two quantities related? | Scatter, log axes if the range spans decades, the frontier or knee annotated | `.dots()` |
| How sure are we? | Shaded interval along a line, or an error bar per point, with n stated | `.band()` or `.err()` + `.dots()` |
| What does the spread look like? | Histogram or dot strip, not a bare mean | `.bars()` on binned data, or `.dots()` |
| What depends on what parameter? | The chart plus one slider that recomputes it | `Fig` + a range input |
| What was the order of events? | Timeline with eras as shaded spans and events as labelled marks | `.span()` + `.dots()` with years as numbers, or hand SVG |
| Who is related to whom, or what contains what? | Tree or nested boundaries | hand SVG |
| How do several things score on several criteria? | Matrix with one row per thing; shade cells only if the scale is real | HTML table |

One question per figure. When a section has two questions, give it two figures or two
views with a toggle; an overloaded diagram answers neither.

## What makes each kind good

### Sequence diagrams

- Three to six actors. More than that and it is really a system diagram with a trace on
  it; split it or group actors.
- Name actors by role as the reader thinks of them ("Optimizer", "Your browser", "Laban"),
  not by class or host name.
- Six to twelve steps. Each label is a short phrase saying what crosses the line, with the
  payload when it matters: `batch x [32, 4096]`, `signed certificate`, `$5,000 transfer`.
- Use `kind: 'return'` for replies so the dashed line reads as a response, and
  `kind: 'self'` for work an actor does alone.
- Put the reasoning in each step's `detail`, not in the label: why this step exists, what
  would break without it, what is not happening (no gradient stored, nothing written).
- Follow it with a sentence naming the one step the whole thing hinges on.
- For alternative paths (success and failure, with and without a cache), draw two
  diagrams side by side or behind a toggle. Branches inside one sequence get unreadable.

### System and architecture diagrams

- Draw the concepts the reader will use afterwards, at the level he will talk about them.
- Encode kind in shape and colour, then state the encoding in the caption: frozen versus
  trained, stored versus computed, yours versus someone else's, trusted versus untrusted.
- Write shapes, sizes or units on the elements: `[batch, seq, d]`, `16.8M params`,
  `4 GB`. For a data scientist these labels often carry more than the boxes do.
- Lay it out in the direction the data or control flows, and keep that direction for every
  diagram on the page.
- Route arrows around boxes and labels. If two arrows mean different things (data and
  gradient, request and response), make them look different and say which is which.
- Make it clickable with `data-explain` when a box has more to say than fits in it.

### Charts of training, experiments and evaluations

- Show the baseline on the same axes, always. A number without its comparison isn't yet
  information.
- Show spread: seeds as thin lines or a band, a metric with its interval, n in the
  subtitle. If the source gives only a point estimate, say that in the caption.
- Use a log axis when the values span more than about two orders of magnitude (parameter
  counts, learning rates, costs, dataset sizes), and let the helper label it as log. For a
  handful of discrete settings (rank 1, 2, 4, ... 64), a categorical `band` axis with one
  tick per setting reads better than a log axis.
- Annotate where the story is: the step where validation loss turns, the rank past which
  gains flatten, the point where one method overtakes another.
- Keep metric direction obvious. Say "lower is better" or "higher is better" in the
  subtitle when it isn't universal.
- Compare like with like: same eval set, same budget, same seed count. If the source's
  comparison isn't like for like, that goes in the caption, not buried at the end.

### Timelines and histories

- Give eras as background bands and events as marks, so the reader sees periods and not
  only points.
- Put parallel tracks on shared time when the story is about how two things relate: model
  releases against harness features, two kingdoms, two countries.
- Make each event clickable or hoverable for its detail, and keep only the pivotal ones
  labelled on the chart itself.
- State uncertain dates as ranges and say whose dating you follow.

### Worked examples

- Small enough to hold in the head: a 4x4 matrix, one training row, one paycheque.
- Carry the same example through every step and show the value at each one, with units.
- Where a formula appears, substitute the numbers on the next line.
- If the page has a slider, make the worked example its default setting, so the text and
  the figure agree.

### Tables

A table is the right figure when the reader needs to look up exact values or compare many
attributes of a few things. Keep it to what will be compared, right-align numbers (the
template's `num` class), sort by the column that matters, and put a one-line takeaway
above it. Offer the table behind each chart with `.table()`.

## Subjects that are not technical

The same approach holds for a passage of Scripture, a period of history or a legal process;
only the vocabulary changes.

- A narrative with several parties is a sequence diagram: who says or does what to whom,
  in order, with the verse or date as the payload.
- Competing positions are a matrix or a two-axis map with each position placed and
  sourced.
- A genealogy or chain of custody is a tree.
- A process with deadlines (a tax filing, a certification) is a timeline with the reader's
  own dates on it.

Keep the page's own claims separate from the sources' claims, quote the text being
explained accurately and briefly, and for contested questions show the main views with who
holds them, without quietly picking one.

## Before adding a figure, and after

Before: say in one sentence what the reader will be able to answer by looking at it. If
the sentence is vague ("gives an overview of the system"), the figure will be too.

After: cover the caption and look at the figure alone. If the point isn't visible without
the caption, the figure needs an annotation, a reordering, or a different form.
