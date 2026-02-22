# 🧠 NeuroBrief

**Agentic Clinical Documentation Intelligence for Psychiatric Care**

*Submitted for MedGemma Impact Challenge - Agentic Workflow Prize Track*

[![Demo](https://img.shields.io/badge/Demo-Live-success)](YOUR_STREAMLIT_URL_HERE)
[![Video](https://img.shields.io/badge/Video-Watch-red)](YOUR_YOUTUBE_URL_HERE)

---

## Overview

NeuroBrief transforms fragmented psychiatric documentation into structured clinical timelines using **MedGemma 1.5** and **agentic workflow orchestration**.

**The Problem:** Psychiatric clinicians spend substantial time reviewing fragmented multi-year documentation across dozens of notes before patient appointments, increasing cognitive load and risk of missing critical patterns.

**The Solution:** An agentic system that extracts, temporally aligns, and synthesizes clinical events while explicitly flagging attribution uncertainty when multiple interventions overlap with outcomes.

---

## Key Innovation: Attribution Uncertainty Detection

When multiple interventions (medication changes, therapy initiation) occur within a temporal window before an outcome change, **NeuroBrief explicitly flags this as attribution uncertainty** rather than inferring causation.

**Why this matters:** Preserves clinical judgment and prevents algorithmic overconfidence in causal claims.

**Example:** Patient's PHQ-9 improves from 18 to 10 within 28 days. During this period, sertraline was increased AND CBT therapy was initiated. NeuroBrief flags both interventions, leaving causal attribution to the clinician.

---

## Features

### 📊 Longitudinal Timeline Extraction
- Medications with dosing information
- Symptom mentions
- Therapy sessions
- Validated assessment scores (PHQ-9, GAD-7)
- Temporal alignment of all clinical events

### ⚠️ Attribution Uncertainty Detection
- 28-day lookback window
- Intervention deduplication
- Explicit uncertainty flagging
- Preserves clinical judgment

### 🔍 Source Traceability
- Every finding links to source note
- Click-through verification
- Transparent extraction

### 📈 Clinical Insights
- Treatment response patterns
- Assessment trajectories
- Automated trend detection

---

## Architecture

```
Clinical Notes → MedGemma Agentic Pipeline → Structured Timeline
                       ↓
         ┌─────────────┴─────────────┐
         │   Specialized Agents      │
         ├───────────────────────────┤
         │  • Event Extraction       │
         │  • Assessment Parsing     │
         │  • Summary Generation     │
         └─────────────┬─────────────┘
                       ↓
         Attribution Uncertainty Detection
         (Rule-based temporal analysis)
                       ↓
         Interactive Visualization
```

### Components

**MedGemma 1.5 Integration**
- Medical language understanding
- Clinical entity extraction
- Dual-mode architecture (real model + demo fallback)

**Agentic Pipeline**
- Specialized agents for different extraction tasks
- Orchestrated workflow via NeuroBriefPipeline
- Parallel processing of events, assessments, and synthesis

**Attribution Detection Algorithm**
- Deterministic rule-based approach
- Temporal window analysis (28 days)
- Intervention deduplication
- Explicit uncertainty flagging

**Interactive Visualization**
- Timeline view with color-coded events
- Medication history panel
- Assessment trajectory charts
- Source traceability interface


## MedASR Integration (Architectural)

**Note:** The current demo focuses on text-based documentation. The full NeuroBrief architecture includes **MedASR** for medical audio transcription, enabling processing of dictated session summaries alongside typed notes.

**MedASR Role:**
- Transcribes clinician dictation with medical-grade accuracy
- Preserves psychiatric terminology and medication dosing
- Feeds into the same MedGemma pipeline as typed notes

**Implementation Status:**
- **Architectural design:** Complete (see writeup)
- **Demo implementation:** Text-only (MedASR requires Google Vertex AI access)
- **Production readiness:** Requires MedASR API integration

The demo demonstrates the core MedGemma-powered agentic workflow. Audio ingestion via MedASR would extend input modalities without changing the underlying pipeline architecture.


---

## Installation

### Quick Start (Demo Mode)
```bash
git clone https://github.com/YOUR_USERNAME/neurobrief.git
cd neurobrief
pip install -r requirements.txt
streamlit run app.py
```

### Full Installation (with MedGemma)
```bash
pip install -r requirements-full.txt
streamlit run app.py
```

Then enable "Use Real MedGemma" in the sidebar (requires GPU with 6GB+ VRAM).

---

## Usage

1. **Select a case** from the dropdown menu
2. **Click "Run Agentic Pipeline"** to process
3. **Explore the timeline:**
   - **Timeline View:** See temporal alignment of all events
   - **Medications:** Review intervention history
   - **Outcomes:** Visualize assessment trajectories
4. **Review attribution uncertainty** in the right panel
5. **Verify sources** by clicking on any event

---

## Project Structure

```
neurobrief/
├── app.py                    # Main Streamlit application
├── medgemma_client.py        # MedGemma integration & extraction logic
├── pipeline.py               # Agentic workflow orchestration
├── attribution.py            # Attribution uncertainty detection
├── prompts.py                # Agent prompt templates
├── requirements.txt          # Demo mode dependencies
├── requirements-full.txt     # Full dependencies with MedGemma
├── README.md                 # This file
└── synthetic_data/           # Synthetic clinical cases
    ├── case_1.json          # Multi-intervention case
    └── case_2.json          # Anxiety treatment case
```

---

## Technical Details

**Model:** MedGemma 1.5 (google/medgemma-1.5-4b-it)  
**Framework:** Streamlit, Plotly, Transformers  
**Visualization:** Plotly interactive charts  
**Attribution Algorithm:** Rule-based temporal window analysis

### Key Algorithm: Attribution Uncertainty Detection

```python
def detect_attribution_uncertainty(events, assessments, window_days=28):
    """
    Flags periods where 2+ interventions preceded assessment changes.
    
    Parameters:
    - events: List of clinical interventions (meds, therapy)
    - assessments: List of validated assessment scores
    - window_days: Lookback period (default: 28 days)
    
    Returns:
    - List of attribution uncertainty flags
    """
    # Implementation in attribution.py
```

---

## Demo

- **📹 Video Demo:** [Add YouTube link here]
- **🌐 Live Demo:** https://medgemma-impact-challenge-neurobrief.streamlit.app
- **📄 Writeup:** Available in competition submission

---

## Competition Details

**Challenge:** MedGemma Impact Challenge  
**Track:** Agentic Workflow Prize ($10,000)  
**HAI-DEF Model:** MedGemma 1.5 (google/medgemma-1.5-4b-it)

### Why This Qualifies for Agentic Workflow Prize

1. **Multiple Specialized Agents:**
   - Event extraction agent
   - Assessment parsing agent
   - Summary generation agent

2. **Orchestrated Workflow:**
   - Pipeline coordinates agent execution
   - Temporal alignment of outputs
   - Synthesis of findings

3. **Real Clinical Value:**
   - Addresses documented clinician pain point
   - Reduces cognitive load
   - Preserves clinical judgment through uncertainty flagging

---

## Data & Safety Notice

**All demonstrations use synthetic clinical data** created specifically for this project. No actual patient information is used or included.

**Disclaimer:** This is a research prototype for competition submission. It is not a medical device, does not provide clinical advice, and should not be used for real patient care.

---

## Requirements

### Demo Mode (Streamlit Cloud)
```txt
streamlit==1.31.0
plotly==5.18.0
pandas==2.1.0
```

### Full Mode (Local with GPU)
```txt
streamlit==1.31.0
plotly==5.18.0
pandas==2.1.0
transformers==4.50.0
torch==2.5.0
accelerate==0.34.0
```

---

## Author

**Yasmin Aboubakr (Jasmine)** 

Software Engineer - Swisscom Devops Centre

MSc Psychology & Neuroscience of Mental Health - King's College London

Bachelor's in Computers and Artificial Intelligence - Cairo University


---

## Acknowledgments

This project was developed for the MedGemma Impact Challenge using HAI-DEF models from Google Health AI.

Special thanks to the competition organizers for creating this opportunity to explore agentic applications of medical AI.

---

## Contact

For questions about this submission, please reach out through the competition platform or GitHub issues.

---

**Built with MedGemma 1.5 🧠 | Agentic Workflow ⚡ | Clinical AI 🏥**
