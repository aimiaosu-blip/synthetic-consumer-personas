"""Strict, explicit provenance and matched-response input contract."""
import csv
import hashlib
import json
import math
from pathlib import Path
from .design import PERSONAS, CONCEPTS

FIELDS = ["respondent_id", "persona_id", "concept_id", "rating", "feedback", "source_type"]

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_reference(path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    kind = manifest.get("source_type")
    if kind not in {"synthetic_demo", "real_public"}:
        raise ValueError("source_type must be synthetic_demo or real_public")
    if kind == "real_public":
        for key in ["source_url", "license", "collected_at", "population", "question", "persona_mapping", "concept_mapping"]:
            if not isinstance(manifest.get(key), str) or not manifest[key].strip():
                raise ValueError("Real data manifest requires " + key)
        if not manifest["source_url"].startswith("https://"):
            raise ValueError("source_url must be an HTTPS public source")
        if manifest.get("deidentified") is not True or manifest.get("holdout") is not True:
            raise ValueError("Real inputs must be deidentified and held out from persona/prompt development")
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or []) != set(FIELDS):
            raise ValueError("CSV must contain exactly: " + ",".join(FIELDS))
        rows = list(reader)
    if not rows:
        raise ValueError("Reference dataset is empty")
    seen, assignments = set(), {}
    for row in rows:
        if any(v is None for v in row.values()) or None in row:
            raise ValueError("Malformed CSV record")
        if not row["respondent_id"].strip() or row["persona_id"] not in PERSONAS or row["concept_id"] not in CONCEPTS:
            raise ValueError("Invalid ID or unknown persona/concept; adapt design explicitly")
        value = float(row["rating"])
        if not math.isfinite(value) or value not in (1, 2, 3, 4, 5):
            raise ValueError("Ratings must be integers 1 through 5")
        row["rating"] = int(value)
        if row["source_type"] != kind:
            raise ValueError("Mixed or mislabeled source types")
        key = (row["respondent_id"], row["concept_id"])
        if key in seen:
            raise ValueError("Duplicate respondent/concept pair")
        seen.add(key)
        previous = assignments.setdefault(row["respondent_id"], row["persona_id"])
        if previous != row["persona_id"]:
            raise ValueError("Respondent has inconsistent persona assignment")
    return rows, manifest

def write_csv(path, rows, fields=FIELDS):
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
