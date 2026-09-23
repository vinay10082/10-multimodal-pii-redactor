# PII Redactor

## Description
A multimodal anonymization engine ensuring irreversible redaction of PII from text and PDF documents.

## Architecture Overview
Integration of Microsoft Presidio (spaCy NER) for contextual detection and PyMuPDF for destructive spatial bounding-box redaction.

## Prerequisites
* Python 3.11+
* `presidio-analyzer`
* `presidio-anonymizer`
* `spacy`
* `pymupdf`

## Environment Variables
* `SPACY_MODEL_NAME`
* `CONFIDENCE_THRESHOLD`
* `REDACTION_FILL_COLOR`

## Quick Start & Usage
Submit a document buffer to the pipeline to receive a fully anonymized, irreversibly redacted output file.

## Testing & CI
Validates entity recognition accuracy and verifies that redacted PDFs yield zero extractable text within the target bounding boxes.
