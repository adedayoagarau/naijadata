# Decide9ja Web App

Budget transparency and accountability tool for Nigerians.

## Features

- 💬 **AI Chat**: Ask questions about any budget
- 🔍 **Budget Explorer**: Search and browse all MDAs
- 🚨 **Red Flag Alerts**: See suspicious spending patterns
- 🎴 **Card Generator**: Create shareable graphics
- 📊 **Compare Tool**: Side-by-side budget comparisons

## Tech Stack

- **Frontend**: Next.js 14 + Tailwind CSS + shadcn/ui
- **AI/RAG**: LangChain + ChromaDB + Claude API
- **Database**: SQLite (budget data)
- **Card Generation**: Satori + Resvg
- **Hosting**: Vercel

## Getting Started

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Add your ANTHROPIC_API_KEY

# Run development server
npm run dev
```

## Project Structure

```
webapp/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Landing page
│   ├── chat/              # AI chat interface
│   ├── explore/           # Budget explorer
│   ├── red-flags/         # Anomaly browser
│   ├── card/              # Card generator
│   └── api/               # API routes
│       ├── chat/          # RAG endpoint
│       ├── search/        # Budget search
│       └── card/          # Card image generation
├── components/            # Reusable UI components
├── lib/                   # Utilities
│   ├── rag/              # RAG pipeline
│   ├── budget/           # Budget data helpers
│   └── cards/            # Card templates
├── data/                  # Budget JSON files
└── public/               # Static assets
```

## Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=file:./data/budget.db
CHROMA_PATH=./data/chroma
```

## Data Pipeline

1. PDF extraction (done via Python scripts)
2. JSON normalization
3. Embedding generation (for RAG)
4. Vector store indexing (ChromaDB)

## API Endpoints

### POST /api/chat
Chat with budget data using RAG.

```json
{
  "message": "How much did NIA spend on hospitals?",
  "history": []
}
```

### GET /api/search
Search budget items.

```
/api/search?q=travel&mda=national+assembly&year=2026
```

### POST /api/card
Generate shareable card image.

```json
{
  "template": "comparison",
  "data": {
    "item1": { "label": "NIA Hospitals", "amount": 31100000000 },
    "item2": { "label": "Health Ministry", "amount": 675900000 }
  }
}
```
