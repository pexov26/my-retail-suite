# 📊 Enterprise Retail Intelligence Suite

A modular, production-grade **Streamlit** analytics application engineered to evaluate transactional retail data, monitor category performance, track inventory trends, and isolate operational drainers [cite: 2].

## 🏗️ Architecture Blueprint
The application strictly adheres to a decoupled 5-layer design pattern to maintain clean separation of concerns:
* `config.py` — Application layout, styles, global definitions, and configuration profiles.
* `data_generator.py` — Optimized multi-year high-volume data simulation engine wrapped in `@st.cache_data`.
* `analytics_engine.py` — Isolated analytical backend processing mathematical calculations and KPIs.
* `app.py` — Presentation layer managing interactive dashboard UI elements and filter matrices.
* `requirements.txt` — Tracked sandbox package ecosystem dependencies.

## 🚀 Local Installation & Quickstart

1. **Clone the Repository:**
   ```bash
   git clone https://github.com
   cd my-retail-suite
   ```

2. **Initialize and Activate Your Environment:**
   ```bash
   # Activate your local custom workspace layout toggle shortcut
   lab
   ```

3. **Launch the Dashboard Application Server:**
   ```bash
   streamlit run app.py
   ```
