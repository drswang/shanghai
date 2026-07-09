# Shanghai 1905 — Manuscript (LaTeX)

LaTeX port of the manuscript *"Non-extreme Rainfall and Tide Synchronization
Driving Compound Coastal Flooding in a Mega-delta."* Intended for Overleaf ↔
GitHub sync.

## Files
| File | Description |
|------|-------------|
| `main.tex` | Main text (21 pp). |
| `supp.tex` | Supplementary text + figure (4 pp). |
| `media_main/media/` | Main-text figure assets (`image2`, `image4`; `.svg` source + `.pdf` used at compile). |
| `media_supp/media/` | Supplement figure (`image1.jpeg`). |
| `latexmkrc` | Forces XeLaTeX (`$pdf_mode = 5`). |

## Compiling
**Requires XeLaTeX** (the text uses Unicode math/symbols such as λ, ≈, °, ×
that pdfLaTeX cannot handle).

```bash
latexmk -xelatex main.tex
latexmk -xelatex supp.tex
```

**On Overleaf:** set *Menu → Compiler → XeLaTeX* (the `latexmkrc` also requests it).

## Provenance
Converted with `pandoc 3.10` from the Word sources in
`OneDrive/Work/Papers_undergoing/Shanghai1905/`:
`maintext_after_SW_LS_QY.docx` and `Supp_Text_Fig.docx` (Dec 2025).
SVGs were rasterized to PDF with `rsvg-convert` for XeLaTeX compatibility.

## Status — faithful port (numbers NOT yet updated)
This is a **verbatim port of the old-simulation manuscript**; it compiles but
still contains the previous results. Known items for the update pass:

- **Results still reflect old simulations.** e.g. abstract "inundated 73% of the
  area", "~2-year and ~5-year return periods" — update to the new
  5-scenario runs (ctrl / no rain #1 / no rain #2 / no rain #1&2 / stone→earth dike).
- **Figures are placeholders** from the old paper. Only **two** figures were
  embedded in the source docx (`image2`, `image4`) plus one supplement image —
  verify all intended figures are present and swap in the regenerated versions.
- **Citations are plain-text author-year** (as in the docx); there are no
  `\cite` commands and **no `.bib` file** here yet. `references.bib` is
  Zotero-linked and maintained separately — wire up `\bibliography{references}`
  and citation keys in a later revision. Any references needing keys will be
  flagged in revision notes, not edited here.
- Affiliation #2 is a placeholder ("yyyyyyyyyyy") carried over from the source.
