# Chapter 27: automated comparison against the live official text (2026-11-14)

> An **automated text comparison**, not a reviewer approval. A citation becomes verified only after the reviewer
> (Naisha Chadha) personally checks it on the official source and explicitly approves it.

- **Source:** Municode, Madison Code of Ordinances, Chapter 27, opened in the user's browser
  (https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO).
  The page shows **"VERSION: SEP 1, 2026 (CURRENT)"**.
- **Same chapter as the PDF export:** 17 section headings (§27.01–§27.13); newest amendments cited are ORD-24-00056 and
  ORD-24-00050 (no 2025/2026 ordinances), the same as `docs/legal/Madison_Chapter_27.pdf`.
- **Method:** the page's full text (~115k characters) was compared word for word with each excerpt, after collapsing
  whitespace and normalizing curly quotes.

## Results
- **All 26 provisional excerpts:** MATCH (plumbing, heat, surfaces, locks, windows, pests, electrical, water damage,
  smoke-alarm reference, exits).
- **Not-mapped excerpts** (§27.04(2)(g)3., §27.05(2)(m)): MATCH.
- **Parse corrections:** the corrected §27.05(2)(h)7. and §27.05(2)(x) texts (from the PDF) MATCH the live text, which
  confirms the parser defects were in the parse, not in the ordinance.
- **Subsection labels:** each excerpt sits under its stated label on the live page, e.g. "(2) Every owner or operator
  shall improve and maintain…" → "(j) Every plumbing fixture…"; "(h) Heating. …"; "(g) 1. Every interior floor…".
- **The ordinance's own references confirm several subsection numbers:** §27.10 lists "Sec. 27.05(2)(j), MGO, Plumbing
  Fixtures and Waste Pipes."; history notes read "(Sec. 27.04(2)(h) Am. by Ord. 9326 …)", "(Sec. 27.04(2)(g) Rescinded &
  Substituted …)", "(Sec. 27.04(2)(f) Am. by …)", "(Sec. 27.05(2)(h) Am. by Ord. 7481 …)"; §27.07(2)(d) and §27.051 cite
  "Sec. 27.05(2)(g)2.". No such internal reference exists for §27.05(2)(g)1., (i), (w), §27.07(2)(c), (d) or §27.04(2)(d):
  those numbers rest on the visible (1)/(a)/1. labels on the page.
- **Still open on the live page:** §27.04(2)(d) still says "except as provided in Sec. 27.06(4), MGO" (the only
  reference to 27.06(4) in the chapter), and §27.06(4) is still about habitable rooms below grade. **Unresolved.**
