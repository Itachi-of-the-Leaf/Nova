<div align="center">
  <!-- <img width="1200" height="475" alt="N.O.V.A. Banner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" /> -->

  <h1>⚡ N.O.V.A.</h1>
  <p><b>Normalized Optimization & Verification Assistant</b></p>
  <p><i>Zero-Hallucination AI Editing & IEEE-Standard Formatting for Academic Research</i></p>

  <div>
    <img src="https://img.shields.io/badge/vite-%23646CFF.svg?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
    <img src="https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB" alt="React" />
    <img src="https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
    <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python" />
    <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=Ollama&logoColor=white" alt="Ollama" />
  </div>
</div>

---

## 🌟 About N.O.V.A.

**N.O.V.A.** is a revolutionary AI-powered academic publishing pipeline. It safely transforms raw manuscript drafts (`.docx`) into pristine, **IEEE Transactions-compliant** outputs without altering the underlying scientific truth of the research. 

Using localized Large Language Models (LLMs) via Ollama, combined with dense vector semantic hashing, N.O.V.A. guarantees **0% scientific hallucination** while optimizing formatting, structure, and text flow.

## ✨ Core Features

*   **🤖 Privacy-First Local AI**: Powered by local models via Ollama. No research data is sent to external cloud APIs, ensuring absolute pre-publication confidentiality.

*   **📑 Automated IEEE Formatting**: Detects manuscript hierarchies, automatically converts them into LaTeX sections, and outputs native IEEE templates natively.
*   **🔒 Cryptographic Integrity Proofs**: Employs deep contextual embeddings (`all-MiniLM-L6-v2`) to compare the lexical and semantic hashes of your original vs. formatted document, mathematically proving that no scientific intent was hallucinated or lost.
*   **🪄 Interactive Verification & Compliance**: Empowers researchers to review metadata extraction (title, authors, abstract, headings) and dynamically adjust text flow before finalizing.
*   **📥 Multi-Format Export**: One-click generation of native `.tex` to `PDF` (via `pdflatex`), alongside structurally compliant `.docx` outputs and downloadable PDF Integrity Reports.

---

## 🏗️ Architecture

```text
NOVA/
├── backend/                       # Python FastAPI Backend
│   ├── data/                      # LaTeX templates and outputs
│   │   ├── IEEEtran.cls           # Native IEEE style class
│   │   └── template.tex           # N.O.V.A. dynamic injector template
│   ├── src/                       
│   │   ├── main.py                # FastAPI routes & endpoints
│   │   ├── engine.py              # LLM extraction & semantic hashing
│   │   └── formatter.py           # LaTeX compilation & DOCX builder
│   └── requirements.txt     
├── frontend/                      # React + Vite Frontend
|   ├── src/
|   │   ├── components/            # Brutalist/Neon Step UI Components
|   │   ├── store/                 # State management
|   │   └── App.tsx                # Application shell
|   └── package.json         
└── assets/                        # Contains all the assets for the project 
    └──TeamNova_Round2.mp4         # Demo video of NOVA

```

---

## 🚀 Getting Started

### Prerequisites

To run N.O.V.A. fully on your machine, you must install the following software:

1.  **[Node.js](https://nodejs.org/)** (v18+) for the frontend application.
2.  **[Python](https://www.python.org/)** (3.10+) for the backend API.
3.  **[Ollama](https://ollama.com/)** running locally to serve AI models.
    *   Pull the required model: `ollama run phi3:mini` (or your chosen model).
4.  **[MiKTeX](https://miktex.org/)** (or TeX Live / MacTeX) installed and added to your system `PATH`. N.O.V.A. requires `pdflatex` to compile IEEE PDFs. Enable "install missing packages on-the-fly" in MiKTeX Console.

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd NOVA/backend
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd NOVA/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure your environment:
   *   Copy `.env.example` to `.env`.
   *   Ensure `VITE_API_URL` points to your backend (default: `http://localhost:8000`).
4. Start the development server:

   ```bash
   npm run dev
   ```

---

## 🛠️ Usage

1. Open the frontend URL in your browser (usually `http://localhost:3000`).
2. Upload a `.docx` manuscript.
3. Review the extracted Title, Authors, Abstract, and Section Headings.
4. Let the Local AI refine and verify text compliance.
5. Review the **Semantic Hash Score** in the Finalization dashboard.
6. Export as IEEE PDF or beautifully formatted DOCX!

## 📄 License
This project is licensed under the MIT License.
