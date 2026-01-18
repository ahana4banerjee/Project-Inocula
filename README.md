# Project Inocula  
**An Agentic AI System for Misinformation & Psychological Manipulation Detection**

---

## Overview
**Project Inocula** is an **agentic AI pipeline** designed to detect **misinformation, psychological manipulation, and deceptive narratives** in digital content.

Instead of relying on a single LLM call, Inocula uses **multiple reasoning agents**, semantic memory, and traditional ML models to analyze *how* misinformation works — emotionally, logically, and contextually.

This project prioritizes **architecture, reasoning depth, and correctness** over quick demos.

---

## Core Philosophy
Most systems ask:
> *“Is this content true or false?”*

Inocula asks:
- How is this content manipulating emotions?
- Which logical fallacies are being used?
- Has this narrative appeared before in a different form?
- What evidence supports or contradicts the claims?

---

## System Architecture

### High-Level Flow
```text
┌────────────┐
│ Input │
│ (Text/Web) │
└─────┬──────┘
│
▼
┌─────────────────┐
│ Detector Agent │
│ Risk + Confidence│
└─────┬───────────┘
│
▼
┌────────────────────────────┐
│ Analyzer Agent │
│ - Emotional Manipulation │
│ - Logical Fallacies │
│ - False Authority │
└─────┬──────────────────────┘
│
▼
┌────────────────────────────┐
│ Verifier Agent │
│ - Wikipedia API │
│ - Fact Check Sources │
└─────┬──────────────────────┘
│
▼
┌────────────────────────────┐
│ Explainer Agent │
│ Structured Reasoning Output│
└──────────┬─────────────────┘
▼
Final Insight

```

---

### Agent Collaboration Model
```text
           ┌──────────────────────┐
           │   Shared Memory      │
           │     (MongoDB)        │
           └─────────┬────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌───────────┐  ┌───────────┐  ┌───────────┐
│ Detector  │  │ Analyzer  │  │ Verifier  │
│   Agent   │  │   Agent   │  │   Agent   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              |              │
      └──────────────┴─────────────-┘
                      │
              ┌──────────────┐
              │  Explainer   │
              │    Agent     │
              └──────┬───────┘
                     │
           Final Reasoned Output

```

Agents operate **statefully**, read from shared memory, and collaborate instead of working in isolation.

---

### Semantic Memory Layer (Planned)


```text
New Content
│
▼
Generate Embedding
│
▼
FAISS Vector Store
│
├── High Similarity → Early Warning
│
▼
Agent Pipeline
```

---

## Current Status
**Early Development / Foundation Phase**

- Agentic refactor in progress
- No deployment yet (intentional)
- Focus on:
  - Correct agent boundaries
  - Tool usage
  - Reasoning transparency
  - Memory design

---

## Roadmap 

### Phase 1 — Agentic Core
- LangGraph-based orchestration
- Stateful agents with memory
- Tool-calling support
- MongoDB-backed state

### Phase 2 — Semantic Memory (current)
- FAISS vector database
- Sentence-transformer embeddings
- Narrative similarity detection

### Phase 3 — Psychological Manipulation ML
- Custom ML classifiers:
  - Emotional manipulation
  - Logical fallacies
- Traditional ML + LLM hybrid

### Phase 4 — Proactive Scanning
- Background analysis
- Async processing (FastAPI + Celery)
- Risk-threshold triggers

### Phase 5 — Multilingual Intelligence
- Language detection
- IndicBERT / mBERT routing
- Indian regional languages

### Phase 6 — Dashboards & Insights
- User exposure profiles
- Emotion trends
- Narrative clustering

### Phase 7 — Engineering Polish
- Dockerization
- Evaluation metrics
- Ethical AI documentation

---

## Tech Stack
- **Agent Framework**: LangGraph / LangChain  
- **LLMs**: Gemini (free tier), HuggingFace models  
- **ML**: scikit-learn / PyTorch  
- **Vector Store**: FAISS (local)  
- **Backend**: FastAPI  
- **Async**: Celery + Redis (local)  
- **Database**: MongoDB  
- **Frontend (Planned)**: Chrome Extension + Analytics Dashboard  

---

## Why Inocula Stands Out
- Agentic reasoning instead of single-shot LLM calls
- Semantic memory for repeated misinformation
- Hybrid ML + LLM pipeline
- Psychological manipulation focus
- Proactive detection design
- Multilingual, India-relevant scope

---

## Repository Notes
- Active development repository
- Commit history reflects learning and iteration
- Deployment will occur **after core reasoning layers stabilize**

---


### 📜 Additional Docs
- [Disclaimer & Ethics](./DISCLAIMER.md)  
- [Setup & Local Run Instructions](./INSTRUCTIONS.md)

---

### Author
**Ahana Banerjee** 
Electronics & Communication Engineering  
Interests: Agentic AI, NLP, ML systems

---

> *Inocula is built to reason before it reacts.*

---
