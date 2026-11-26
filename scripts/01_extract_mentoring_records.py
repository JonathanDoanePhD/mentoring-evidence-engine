"""Stage 0a: stream every ERIC XML file and keep records that mention mentoring anywhere
(title, abstract or subject descriptors). Later files can update earlier records, so the
last version of each accession number wins.

python3 -I scripts/01_extract_mentoring_records.py -> data/interim/mentor_records.jsonl
"""
import glob
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "eric"
INTERIM = ROOT / "data" / "interim"
INTERIM.mkdir(parents=True, exist_ok=True)
NS = {"dc": "http://purl.org/dc/elements/1.1/", "dcterms": "http://purl.org/dc/terms/", "eric": "http://www.eric.ed.gov"}
MENTOR = re.compile(r"mentor", re.I)


def text(el, path):
    x = el.find(path, NS)
    return (x.text or "").strip() if x is not None and x.text else ""


def texts(el, path):
    return [x.text.strip() for x in el.findall(path, NS) if x is not None and x.text and x.text.strip()]


records, scanned = {}, 0
for f in sorted(glob.glob(str(RAW / "eric[0-9][0-9][0-9][0-9].xml"))):
    for _, rec in ET.iterparse(f, events=("end",)):
        if rec.tag != "record":
            continue
        scanned += 1
        md = rec.find("metadata")
        if md is not None:
            title, desc = text(md, "dc:title"), text(md, "dc:description")
            subj = texts(md, "dc:subject")
            if MENTOR.search(title) or MENTOR.search(desc) or any(MENTOR.search(s) for s in subj):
                acc = ""
                for idn in md.findall("dc:identifier", NS):
                    if idn.get("scheme") == "eric_accno":
                        acc = (idn.text or "").strip()
                urls = [i.text.strip() for i in md.findall("dc:identifier", NS) if i.get("scheme") == "dcterms:URI" and i.text]
                records[acc] = {
                    "id": acc, "title": title, "abstract": desc, "subjects": subj,
                    "types": texts(md, "dc:type"), "levels": texts(md, "dcterms:educationLevel"),
                    "year": text(md, "dc:date")[:4], "source": text(md, "dc:source"),
                    "peer_reviewed": text(md, "eric:peer_reviewed") == "T",
                    "wwc_reviewed": text(md, "eric:wwc_reviewed"), "doi_or_url": urls[0] if urls else "",
                    "ies_funded": text(md, "eric:ies_funded") == "Yes", "file": Path(f).name,
                }
        rec.clear()
    print(f"{Path(f).name}: scanned so far {scanned:,}, mentoring records {len(records):,}", flush=True)

with open(INTERIM / "mentor_records.jsonl", "w") as out:
    for r in records.values():
        out.write(json.dumps(r) + "\n")
print(f"done: {scanned:,} records scanned, {len(records):,} mention mentoring")
