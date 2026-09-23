"""Command-line entry point for irreversible PII redaction."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".json", ".log"}


@dataclass(frozen=True)
class Settings:
    spacy_model_name: str
    confidence_threshold: float
    redaction_fill_color: tuple[float, float, float]
    language: str

    @classmethod
    def from_environment(cls) -> "Settings":
        model_name = os.getenv("SPACY_MODEL_NAME", "en_core_web_sm")
        language = os.getenv("LANGUAGE", "en")
        try:
            threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))
        except ValueError as error:
            raise ValueError("CONFIDENCE_THRESHOLD must be a number between 0 and 1") from error
        if not 0 <= threshold <= 1:
            raise ValueError("CONFIDENCE_THRESHOLD must be between 0 and 1")

        raw_color = os.getenv("REDACTION_FILL_COLOR", "0,0,0")
        try:
            color = tuple(float(part.strip()) for part in raw_color.split(","))
        except ValueError as error:
            raise ValueError("REDACTION_FILL_COLOR must contain three numbers, such as 0,0,0") from error
        if len(color) != 3 or any(not 0 <= component <= 1 for component in color):
            raise ValueError("REDACTION_FILL_COLOR values must be between 0 and 1")
        return cls(model_name, threshold, color, language)


class PIIRedactor:
    """Detect PII with Presidio and redact text or PDF content permanently."""

    def __init__(self, settings: Settings) -> None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_anonymizer import AnonymizerEngine

        self.settings = settings
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": settings.language, "model_name": settings.spacy_model_name}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[settings.language])
        self.anonymizer = AnonymizerEngine()

    def redact_text(self, text: str) -> str:
        results = self._analyze(text)
        return self.anonymizer.anonymize(text=text, analyzer_results=results).text

    def redact_pdf(self, input_path: Path, output_path: Path) -> int:
        import pymupdf as fitz

        document = fitz.open(input_path)
        redaction_count = 0
        try:
            for page in document:
                page_text = page.get_text("text")
                results = self._analyze(page_text)
                word_data = page.get_text("words")
                for result in results:
                    for rectangle in self._rectangles_for_result(word_data, result):
                        page.add_redact_annot(rectangle, fill=self.settings.redaction_fill_color)
                        redaction_count += 1
                page.apply_redactions()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            document.save(output_path, garbage=4, clean=True, deflate=True)
        finally:
            document.close()
        return redaction_count

    def _analyze(self, text: str) -> list[Any]:
        return [
            result
            for result in self.analyzer.analyze(
                text=text,
                language=self.settings.language,
                score_threshold=self.settings.confidence_threshold,
            )
            if result.end > result.start
        ]

    @staticmethod
    def _rectangles_for_result(
        words: Iterable[tuple[float, float, float, float, str, int, int, int]],
        result: Any,
    ) -> list[Any]:
        import pymupdf as fitz

        rectangles: list[Any] = []
        page_offset = 0
        for x0, y0, x1, y1, word, *_ in words:
            word_start = page_offset
            word_end = word_start + len(word)
            if word_end > result.start and word_start < result.end:
                rectangles.append(fitz.Rect(x0, y0, x1, y1))
            page_offset = word_end + 1
        return rectangles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Irreversibly redact PII from text files and PDFs.")
    parser.add_argument("input", type=Path, help="Input .pdf, .txt, .md, .csv, .json, or .log file")
    parser.add_argument("output", type=Path, help="Output file path")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    input_path: Path = args.input
    output_path: Path = args.output
    if not input_path.is_file():
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        return 2
    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Unsupported input type: {input_path.suffix or '(none)'}", file=sys.stderr)
        return 2
    if input_path.resolve() == output_path.resolve():
        print("Input and output paths must be different.", file=sys.stderr)
        return 2

    try:
        from dotenv import load_dotenv

        load_dotenv()
        settings = Settings.from_environment()
        redactor = PIIRedactor(settings)
        if input_path.suffix.lower() == ".pdf":
            count = redactor.redact_pdf(input_path, output_path)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            text = input_path.read_text(encoding="utf-8")
            output_path.write_text(redactor.redact_text(text), encoding="utf-8")
            count = 1
    except Exception as error:  # Keep CLI failures readable for missing models or malformed documents.
        print(f"Redaction failed: {error}", file=sys.stderr)
        return 1

    print(f"Redacted {count} region(s): {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())