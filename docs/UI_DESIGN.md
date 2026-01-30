# Decide9ja - UI Design Document

## Brand Identity

**Name**: Decide9ja (or "Budget Tracker 9ja")
**Tagline**: "See where your money goes"
**Colors**:
- Primary: Green (#008751 - Nigerian flag)
- Secondary: White (#FFFFFF)
- Accent: Gold (#FFC72C)
- Alert/Red Flag: Red (#E63946)
- Dark: #1A1A2E

## Pages & Components

### 1. Landing Page
```
┌─────────────────────────────────────────┐
│  🇳🇬 Decide9ja                    [Menu] │
├─────────────────────────────────────────┤
│                                         │
│     "See Where Your                     │
│      Money Goes"                        │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 💬 Ask about any budget...      │   │
│  │    "How much did NIA spend on   │   │
│  │     hospitals?"                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [🔍 Explore Budgets] [🚨 Red Flags]   │
│                                         │
├─────────────────────────────────────────┤
│  🔥 TRENDING DISCOVERIES                │
│  ┌─────────────────────────────────┐   │
│  │ NIA spending ₦31B on hospitals  │   │
│  │ while Health Ministry gets      │   │
│  │ ₦675M for same purpose          │   │
│  │                     [See More →]│   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 2. Chat Interface
```
┌─────────────────────────────────────────┐
│  ← Back         Budget Chat      [Share]│
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🤖 Welcome! Ask me anything     │   │
│  │    about Nigerian budgets.      │   │
│  │                                 │   │
│  │    Try: "Compare NASS travel    │   │
│  │    budget to Health drugs"      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 👤 How much is NIA spending     │   │
│  │    on hospitals in 2026?        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🤖 In the 2026 Budget Bill,     │   │
│  │    the National Intelligence    │   │
│  │    Agency (NIA) has ₦31.1B      │   │
│  │    allocated for "Hospital      │   │
│  │    Rehabilitation"              │   │
│  │                                 │   │
│  │    📊 This is 46x MORE than     │   │
│  │    Health Ministry's ₦675M      │   │
│  │                                 │   │
│  │    [🎴 Generate Card]           │   │
│  │    [📖 See Full Details]        │   │
│  └─────────────────────────────────┘   │
│                                         │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │ Type your question...       [→] │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 3. Share Card Generator
```
┌─────────────────────────────────────────┐
│  ← Back       Create Card        [Save] │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ┌─────────────────────────────┐ │   │
│  │ │  🚨 BUDGET ALERT             │ │   │
│  │ │                              │ │   │
│  │ │  NIA Hospital Budget         │ │   │
│  │ │  ₦31.1 BILLION              │ │   │
│  │ │                              │ │   │
│  │ │  vs                          │ │   │
│  │ │                              │ │   │
│  │ │  Health Ministry Hospitals   │ │   │
│  │ │  ₦675 MILLION               │ │   │
│  │ │                              │ │   │
│  │ │  ━━━━━━━━━━━━━━━━━━━━━━━━━  │ │   │
│  │ │  That's 46x MORE! 😱         │ │   │
│  │ │                              │ │   │
│  │ │  ₦31B could build:           │ │   │
│  │ │  🏥 207 health centers       │ │   │
│  │ │  🚰 6,220 boreholes          │ │   │
│  │ │  🚑 622 ambulances           │ │   │
│  │ │                              │ │   │
│  │ │  #Decide9ja #OpenBudget     │ │   │
│  │ └─────────────────────────────┘ │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Style: [Dark ▼]  Size: [Square ▼]     │
│                                         │
│  [📱 Share to WhatsApp]                 │
│  [🐦 Share to Twitter]                  │
│  [💾 Download Image]                    │
│                                         │
└─────────────────────────────────────────┘
```

### 4. Red Flags Browser
```
┌─────────────────────────────────────────┐
│  🚨 Red Flags          [Filter ▼] 2026  │
├─────────────────────────────────────────┤
│  Found 177 anomalies worth ₦86.03B      │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🔴 CRITICAL                     │   │
│  │ National Intelligence Agency    │   │
│  │ Hospital Repairs: ₦31.1B        │   │
│  │ "Spy agency spending on health" │   │
│  │                    [Details →]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🔴 CRITICAL                     │   │
│  │ Police Academy Wudil            │   │
│  │ School Meal Subsidy: ₦5.9B      │   │
│  │ "Police subsidizing schools"    │   │
│  │                    [Details →]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🟠 HIGH                         │   │
│  │ Nigerian Army                   │   │
│  │ Road Construction: ₦3.72B       │   │
│  │ "Should be under Works Ministry"│   │
│  │                    [Details →]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Load More...]                         │
└─────────────────────────────────────────┘
```

## Card Templates

### Template 1: Comparison Card
- Two items side by side
- Ratio highlighted
- Impact statement
- Branding footer

### Template 2: Single Stat Card
- One shocking number
- Context
- "What this could build"

### Template 3: Red Flag Alert
- Warning styling
- MDA name
- Suspicious item
- Why it's flagged

## Mobile Optimizations

1. **Bottom navigation** (thumb-friendly)
2. **Large touch targets** (min 44px)
3. **Swipeable cards**
4. **Pull to refresh**
5. **Offline mode** (cached data)
6. **Share sheet integration**

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **Animations**: Framer Motion
- **Charts**: Recharts or Chart.js
- **Card Generation**: html-to-image or Satori
- **AI/RAG**: LangChain + ChromaDB + Claude API
- **Database**: SQLite (simple) or Supabase (scalable)
- **Hosting**: Vercel (frontend) + Railway (backend)
