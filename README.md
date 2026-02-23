<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/9f3acdc7-f157-43af-bb43-185c14b635d5

## Run Locally

**Prerequisites:**  Node.js
## 📁 Project Structure
```
NOVA/
├── backend/                 # Python Flask/FastAPI Backend
│   ├── data/                # Static assets, LaTeX templates, and logs
│   │   ├── IEEEtran.cls
│   │   ├── template.tex
│   │   └── output.log
│   ├── src/                 # Core backend logic
│   │   ├── app.py           # API Entry point
│   │   ├── engine.py        # Processing logic
│   │   └── formatter.py     # Document formatting utilities
│   └── requirements.txt     # Python dependencies
├── frontend/                # React + Vite Frontend
│   ├── src/
│   │   ├── components/      # UI Components
│   │   │   └── steps/       # Workflow steps (Upload, Verify, etc.)
│   │   ├── App.tsx          # Main React component
│   │   └── main.tsx         # Frontend entry point
│   ├── .env                 # Local environment variables (ignored by Git)
│   ├── .env.example         # Template for environment variables
│   └── package.json         # Node.js dependencies
├── .gitignore               # Global workspace ignore rules
└── README.md                # Project documentation
```
1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`
