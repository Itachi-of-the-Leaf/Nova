# DEFECT LEDGER

## Phase 1: The Citation Crash (Backend Debugging)
**Symptoms:** The frontend React UI throws "Error verifying citations" due to a suspected backend 500 error or a malformed Crossref API request payload.
**Root Cause Hypothesis:** The chunking regex implemented previously is likely passing an improperly formatted string or an empty array to `verify_references_block`, causing a crash on the Crossref network request or in the parsing logic.
**Target Status:** UNRESOLVED

## Phase 2: Strict Spatial Reconstruction

### Defect A: Abrupt Paragraph Breaks
**Symptoms:** Sentences are breaking mid-way (e.g., "for \n detachment"). 
**Root Cause Hypothesis:** The unstructured text extractor is outputting hard line breaks at the natural visual end of a page/column, and our post-processor is failing to join lines that don't end in terminal punctuation.
**Target Status:** UNRESOLVED

### Defect B: Table 1 Flattening
**Symptoms:** Tables are rendering as continuous text streams instead of structured grids.
**Root Cause Hypothesis:** The `unstructured` library is failing to correctly utilize the `hi_res` and `yolox` models to extract HTML boundaries, or the `formatter.py` transpiler is failing to construct the `\begin{table}` environment with correct row/col delimiters.
**Target Status:** UNRESOLVED

### Defect C: Header Hallucination
**Symptoms:** The title appears twice, and spurious text like "B. Research paper" is hallucinated as a header.
**Root Cause Hypothesis:** Local fallback logic or the LLM is guessing headers across the entirety of the document. The spatial extraction logic is either disabled or overridden by later passes. We must restrict title detection strictly to the first block at the top of Page 1.
**Target Status:** UNRESOLVED
