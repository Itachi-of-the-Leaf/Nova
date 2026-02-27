# DEFECT LEDGER

## Roadmap

### Target 1: The Citation Data Flow Disconnect
- **Status:** In Progress
- **Defect:** Citations bundled into massive strings by Compliance step, causing Crossref issues.
- **Fix:** Trace extraction and ensure newline-separated citations are mapped into a strictly defined JSON array.

### Target 2: The Citation State Loss (Severance)
- **Status:** In Progress
- **Defect:** React UI changes ("Accept Suggestion", etc.) ignored in final downloaded PDF.
- **Fix:** Ensure final POST request injects the React state payload into formatter.py/LaTeX rendering, discarding original extraction.
