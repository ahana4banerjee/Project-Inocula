# Project Inocula 

A Digital Immune System Against Misinformation for **Mumbai Hacks 2025**

---

###  The Problem

Misinformation spreads faster than facts, manipulating public opinion, fueling panic, and eroding trust—especially during crises.  
Current fact-checking systems are **reactive**, addressing fake news only after it has gone viral and the damage is done.

---

###  Our Solution: A Proactive Immune System

**Project Inocula** is an Agentic AI system that acts like a digital immune system for the internet.  
Instead of just reacting to lies, it proactively identifies emerging misinformation campaigns, analyzes their psychological tactics, and warns users before they are exposed — building cognitive resistance.

---

### Features (Hackathon MVP)

Our fully functional prototype demonstrates the end-to-end flow of our system:

- **Browser Extension:** Extracts content from any live webpage for on-demand analysis.  
- **Multi-Agent AI Backend:** A FastAPI server orchestrating multiple AI agents:
  - **Heuristics Engine:** Detects obvious clickbait (e.g., excessive caps/punctuation).
  - **Detector Agent:** A *toxic-bert* model analyzing harmful patterns (proxy for misinformation).
  - **Analyzer Agent:** Emotion-detection model identifying manipulative tactics (fear, anger).
  - **Explainer Agent:** A Gemini-powered LLM that summarizes the findings in plain English.
- **User Dashboard:** View scan history and submit reports for re-evaluation.
- **Admin Dashboard:** Review reports, view analytics, and flag to official moderation APIs.

---

### Tech Stack

**Frontend:** React, Chart.js, Chrome Extension SDK (Manifest V3)  
**Backend:** Python (FastAPI)  
**AI Models:** Hugging Face Transformers (toxic-bert, emotion-english), Google Gemini  
**Database:** MongoDB Atlas  
**Deployment:** Render (Backend), Netlify (Frontend)

---

### Future Roadmap

Our MVP proves the core concept. The next steps to build a production-ready system include:

- **Proactive Scanning Worker:** Continuously monitors high-risk sources (Reddit, X).  
- **Fact-Checking API Integration:** Cross-references with trusted sources (PolitiFact, Google Fact Check).  
- **User Authentication:** Personalized history, credibility levels, and feedback loops.  
- **Real-Time Notifications:** WebSocket updates when a trending misinformation topic is detected.

---

### 📜 Additional Docs
- [Disclaimer & Ethics](./DISCLAIMER.md)  
- [Setup & Local Run Instructions](./INSTRUCTIONS.md)

---

### Authors
**Ahana Banerjee** 
**Prathik Kumar**   
Contributors: Team DreamDeployers | MumbaiHacks 2025

---
