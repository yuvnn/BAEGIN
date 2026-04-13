# Data Flow

1. monitoring-service collects papers by keyword and journal rules
2. Paper-service evaluates and summarizes papers, manages registration, and stores vectors in Chroma
3. Paper-service runs similarity checks against internal documents
4. comparepdf-service compares papers with internal documents and generates comparison reports
5. comparepdf-service stores comparison outputs in Chroma
6. Save result as JSON/TXT and expose to UI
