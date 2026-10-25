# English pass

Run this on all english text: on the source before you write the lead or translate anything when english is the source, and on the english translation when it is not. The pass has two parts. The first part comes from `simple-english`. The second part comes from `pstack:unslop` and covers only what `simple-english` does not.

If the `simple-english` skill is installed, use it in Plain mode for part 1. If it is not installed, apply the summary below. `pstack:unslop` cannot be called by an agent (`disable-model-invocation`), so part 2 is always this file.

Never change code, identifiers, commands, flags, file paths, quoted errors, product names, numbers, or text quoted from another person.

## Part 1: simple-english (Plain mode)

1. Procedural text (what to do): imperative, 20 words per sentence at most, one instruction per sentence. Descriptive text (what is true): 25 words per sentence at most.
2. Condition before command: "If the build fails, read the log."
3. Simple tenses and active voice. "has completed" becomes "completed". Name the actor.
4. Modals: can, will, must. Not should, would, may, might, could.
5. No contractions. Keep articles and "that".
6. No semicolons and no em-dashes. Write two sentences.
7. One word for one meaning in the whole post. Use "make sure that" for check, verify, confirm, ensure.
8. Define a concept term at first use in a few words. Do not define product names.
9. State the fact, not its importance. Delete simply, seamlessly, robust, crucial, leverage, "in order to", "it is worth noting".

## Part 2: unslop, the rules that part 1 does not cover

1. Colons only before a list or an example. Exception: the "original" label in a two-language lead (`原文:`).
2. A bold label is allowed when it names an item and new detail follows (`**Decision 2:** we split only if ...`). A bold label that restates the line is not allowed.
3. Sentence case in headings.
4. Straight quotes, not curly quotes.
5. No decorative emoji. Exception: the flag in each block title and the 🪴 in the footer.
6. No metaphor nouns where a plain word exists: substrate, wedge, vector, surface (as in "API surface"), north star, flywheel, ratchet, endgame.
7. No mannered prose: aphorisms, personified code ("the plan holds it"), figurative verbs ("rides along").
8. No over-compression: no arrows or symbols in place of verbs, no dropped articles. Exception: a one-line order of steps, like `A → B → C`.
9. No "not just X, but Y", no forced groups of three, no synonym cycling, no vague attributions ("some people think").
10. No chatbot phrases and no sycophancy: "Great question", "I hope this helps", "Let me know if".

## Where the two skills disagree

- "may": unslop allows it, simple-english does not. Follow simple-english.
- Parentheses: unslop discourages them, simple-english allows them. Allow them for a short definition or an example.
