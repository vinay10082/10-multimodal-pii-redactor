# PII Redactor

## Description
A command-line anonymization engine that detects PII with Microsoft Presidio and irreversibly removes it from text and PDF documents.

## Architecture Overview
Integration of Microsoft Presidio (spaCy NER) for contextual detection and PyMuPDF for destructive spatial bounding-box redaction.

## Prerequisites
* Python 3.11+
* The English spaCy model: `python -m spacy download en_core_web_sm`

Install the dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Environment Variables
The default values are provided in `.env`:

* `SPACY_MODEL_NAME`: installed spaCy model name
* `CONFIDENCE_THRESHOLD`: Presidio score threshold from `0` to `1`
* `REDACTION_FILL_COLOR`: PDF fill color as normalized RGB, for example `0,0,0`
* `LANGUAGE`: Presidio language code

## Quick Start & Usage
`main.py` is the entry point. Pass an input path and a different output path:

```bash
python main.py input.pdf output.pdf
python main.py input.txt output.txt
```

Supported text formats are `.txt`, `.md`, `.csv`, `.json`, and `.log`. PDF redactions are applied and saved with garbage collection so the original text is not retained in the output document.

