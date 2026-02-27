# Discovered Defects Ledger

1. **Unstructured Deprecation Warning**: In `engine.py`, `pdf_infer_table_structure=True` triggers a deprecation warning inside Unstructured. Fixed by changing to `skip_infer_table_types=["pdf"]`.
2. **Missing Loading State on React UI**: `UploadStep.tsx` or similar did not originally have robust visual feedback during the blocking `extract_text_from_docx` call (if applicable, ensuring we capture this UX).
3. **Crossref Auto-Correction Bug**: Original `verifier.py` was being called during Verify Structure, causing unwanted side-effects before compliance. Refactored out.
