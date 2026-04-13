# Data Flow

1. User or admin uploads internal docs (PDF, DOCX, planning docs)
2. pdf-service extracts text and splits it into chunks
3. Embeddings are generated and stored in Chroma collection internal_docs
4. monitoring-service polls external paper providers for new papers
5. Paper abstract/full text is stored in Chroma collection papers
6. When compare is requested:
   - search paper vectors
   - search internal doc vectors
   - generate comparison report from similarity + evidence snippets
7. Save result as JSON/TXT and expose to UI
