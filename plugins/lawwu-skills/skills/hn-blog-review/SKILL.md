---
name: hn-blog-review
description: Generate 10-20 realistic Hacker News-style comments on a draft blog post to stress-test arguments, find weaknesses, and improve writing before publishing. Use when reviewing, critiquing, or stress-testing a blog post draft, or when asked to simulate HN feedback, comments, or reactions. Triggers on phrases like "HN comments", "Hacker News review", "stress test this post", "simulate comments", "critique this draft", "how would HN react".
---

# HN Blog Review

Generate realistic Hacker News comments on a blog post draft to surface weaknesses before publishing.

## Input

Accept the blog post as:
- A file path (read it)
- A URL (fetch it)
- Pasted text in the conversation

## Process

1. Read the full post carefully. Identify: thesis, key claims, evidence quality, tone, audience, technical depth, and any weak spots.
2. Read `references/hn-archetypes.md` for commenter personas and thread patterns.
3. Generate 10-20 comments using a realistic mix of archetypes. Follow the quality spectrum: ~30% high-signal, ~40% medium, ~30% low-signal.
4. Include 2-3 reply threads (2-4 comments deep) where commenters disagree with each other.
5. After the simulated thread, provide a **Post-Mortem** section.

## Output Format

```markdown
## Simulated HN Thread: "[Post Title]"

**[username1]** [points] points | [time] ago
[comment text]

  **[username2]** [points] points | [time] ago
  [reply to username1]

    **[username3]** [points] points | [time] ago
    [reply to username2]

**[username4]** [points] points | [time] ago
[another top-level comment]

---

## Post-Mortem

### Strongest Critiques
- [Bullet list of the most valid criticisms from the thread]

### Weakest Points in Your Post
- [Specific sections or claims that would draw the most fire]

### Suggested Improvements
- [Concrete edits to preempt the strongest objections]

### What Landed Well
- [Parts that even skeptics would appreciate]
```

## Guidelines

- **Usernames**: Use realistic HN-style handles (lowercase, short — e.g., `tptacek`, `dang`, `throwaway9182`, `systems_guy`, `mlresearcher`). Do not use real HN usernames.
- **Point counts**: Vary realistically (1-250). Top comments get more; controversial ones stay low.
- **Tone calibration**: HN skews technical, skeptical, and terse. Avoid sycophancy — HN rarely says "great post!" without a "but."
- **Be genuinely critical**: The goal is to find real weaknesses. Pull no punches. If the post has a logical gap, exploit it. If a claim is unsupported, call it out.
- **Match the post's domain**: AI posts get AI-savvy commenters. Finance posts get finance folks. Adjust archetype mix to the subject matter.
- **Length variety**: Mix one-liners with multi-paragraph responses.
