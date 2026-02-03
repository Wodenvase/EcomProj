HashTrack: The E-Commerce Identity Engine
=======================================

Protecting Online Shoppers from "Digital Impersonation" & Retail Fraud

Overview
--------

**HashTrack** is a browser-based cybersecurity tool designed to detect fraudulent e-commerce websites in real-time. Unlike traditional antivirus software that scans for malware files, HashTrack analyzes the **behavioral and structural "DNA"** of a website to determine if it is a legitimate business or a "fly-by-night" scam operation.

- The Problem: E-commerce fraud is moving away from "hacking" users to "social engineering" them. Fake stores (e.g., `nike-clearance-sale-24.com`) look identical to real ones but exist solely to harvest credit card data.
- The Solution: An MLOps-driven browser extension that acts as a "Trust Meter," overlaying a safety score (0-100) on every shopping site visited.

Tech Stack
----------

Hybrid Architecture: a lightweight client (Extension) for speed, backed by a heavy-duty server (Python/ML) for intelligence.

Frontend (The Chrome Extension)

- Language: JavaScript (ES6+), HTML5, CSS3.
- Framework: Manifest V3 (Chrome Extensions).
- State Management: Chrome Storage API (local caching of scores for 24 hours).
- UI Components: Shadow DOM (inject the Trust Score badge without breaking site CSS).

Backend (The Intelligence Engine)

- Language: Python 3.10+.
- API Framework: FastAPI (async, high-performance).
- Server: Uvicorn (ASGI server).

Data & Machine Learning

- ML Libraries: Scikit-Learn (Random Forest / XGBoost), Pandas, NumPy.
- Feature Extraction: `python-whois`, `ssl`, `beautifulsoup4`, `requests`.
- Caching Layer: Redis (real-time caching for computed domain scores).

System Architecture & Logic Flow
-------------------------------

1. Trigger: User navigates to a URL (e.g., `example-store.com`).
2. Local Check: The Extension checks `chrome.storage` for a cached score (valid 24 hours).
   - If cached: display immediately.
   - If not: send `POST /analyze` to the Backend API.
3. Backend Processing ("Hash" Logic):
   - Step A (Registry Check): Query WHOIS. Is the domain < 30 days old? (High risk)
   - Step B (Security Check): Inspect SSL. Is it a free "Let's Encrypt" cert on a bank-like site? (High risk)
   - Step C (Content Check): Scrape the homepage. Look for physical address, working social links, contact info.
   - Step D (ML Prediction): Feed engineered features into the pre-trained classifier.
4. Response: API returns JSON with `domain`, `trust_score`, `risk_level`, and `reasons`.
5. Visual Output: The Extension injects a colored Trust Badge and, if needed, a warning banner.

Trust Algorithm (Feature Engineering)
------------------------------------

We use a Weighted Risk Model to compute a risk score from multiple feature categories.

Feature table (summary):

| Feature Category | Logic / Check | Risk Weight |
| --- | --- | --- |
| Domain Age | Created < 30 days ago | **+40 (Critical)** |
| Domain Age | Created < 6 months ago | +15 (Moderate) |
| SSL Certificate | Issuer is "Let's Encrypt" / "cPanel" | +10 (Low - common but sus for big brands) |
| Visuals | "Copyright 2023" (Outdated) | +5 |
| Social Proof | Social Media icons are broken links | **+25 (High)** |
| Contact Info | No physical address / Phone number found | +20 (High) |
| Urgency Tactics | Keywords: "Hurry", "Counter", "Limited Time" | +10 |

Scoring interpretation:

- 0 - 20 Risk Points: ✅ Safe (Green)
- 21 - 50 Risk Points: ⚠️ Caution (Yellow)
- 51+ Risk Points: 🛑 DANGER (Red)

Directory Structure
-------------------

```
hashtrack/
├── backend/                  # The Brain (Python/FastAPI)
│   ├── app/
│   │   ├── main.py           # API Entry point
│   │   ├── model.py          # ML Model inference logic
│   │   ├── scanner.py        # Feature extraction (Whois, SSL, Scraper)
│   │   └── utils.py          # Helper functions
│   ├── models/               # Saved ML models (.pkl files)
│   ├── cache/                # Redis connection logic
│   ├── requirements.txt
│   └── Dockerfile            # For deployment on Render/Railway
│
├── extension/                # The Face (Chrome Extension)
│   ├── manifest.json         # Configuration
│   ├── background.js         # Event listeners
│   ├── content.js            # The script that injects the UI
│   ├── popup.html            # Clickable popup menu
│   ├── styles.css            # Styling for the Trust Badge
│   └── icons/
│
├── notebooks/                # The Lab (Data Science)
│   ├── 01_data_collection.ipynb   # Gathering phishing/safe URLs
│   ├── 02_feature_extraction.ipynb # Building the dataset
│   └── 03_model_training.ipynb     # Training the Random Forest
│
└── README.md
```

Development Roadmap
-------------------

Phase 1: The Scanner (Days 1-3)

- Build `scanner.py`.
- Implement `get_domain_age(url)`, `check_ssl(url)`, `find_broken_links(url)`.
- Test manually against known scam sites.

Phase 2: The API (Days 4-5)

- Wrap the scanner in FastAPI.
- Create the `/analyze` endpoint.
- Test with Postman.

Phase 3: The Extension (Days 6-7)

- Create the Manifest V3 extension.
- Connect it to the localhost API.
- Design the Trust Badge CSS and Shadow DOM injection.

Phase 4: Production (Day 8+)

- Train the final ML model using PhishTank and Tranco datasets.
- Deploy the API to a cloud provider.
- Publish the extension to the Chrome Web Store.

API Response Example
--------------------

```json
{
  "domain": "example-store.com",
  "trust_score": 15,
  "risk_level": "CRITICAL",
  "reasons": ["Domain created 2 days ago", "Broken social links"]
}
```

Next Steps
----------

- Implement `scanner.py` feature extractors in `backend/app/scanner.py`.
- Scaffold `backend/app/main.py` with a `/analyze` FastAPI endpoint.
- Create a minimal Manifest V3 extension in `extension/` that calls the local API and injects the badge.

License & Notes
---------------

This README is intended as the technical blueprint for development and research. Keep model files and sensitive API keys out of version control; use environment variables or a secrets manager for deployment.

Happy hacking — and stay safe out there!
