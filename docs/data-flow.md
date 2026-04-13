# Data Flow

1. monitoring-service collects papers by keyword and journal rules
2. paper-service evaluates and summarizes papers, manages registration, and stores vectors in Chroma
3. paper-service runs similarity checks against internal documents
4. internal-service compares papers with internal documents and generates comparison reports
5. internal-service stores comparison outputs in Chroma
6. Save result as JSON/TXT and expose to UI
