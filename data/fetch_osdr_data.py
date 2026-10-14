#!/usr/bin/env python3
"""Fetch the real NASA OSDR data for the Veggie studies.

This replaces a version of this file that did not use the archive. It contacted
the OSDR API, logged a simulated failure, and returned values written as Python
tuple literals in the source -- originally produced by ``numpy.random.normal()``,
later replaced by hand-typed numbers that still did not match the archive. Both
versions produced a table that does not exist in OSDR: 36 lettuce samples against
the archive's 24, calcium roughly three times the measured value, a copper column
for a study that never measured copper, and no boron column for a study that did.

What this version does differently
----------------------------------

* **It downloads and uses the archive.** Filenames are resolved from each study's
  OSDR file listing; the bytes are read from the datamanager endpoint. Nothing
  numeric is typed into this file.
* **There is no synthetic fallback.** A failed download raises. A pipeline that
  cannot obtain its data must stop, not substitute numbers that look like data.
* **Unmeasured elements stay empty.** OSD-745 measured neither aluminium nor
  copper, so those columns are absent for lettuce rather than filled with
  plausible values. OSD-745 did measure boron, which the previous version omitted.
* **The OSD-655 unit defect is corrected explicitly.** Five columns are labelled
  ``milligram_per_gram_of_dry_weight`` and are not mg/g -- read that way, mean
  potassium is 2,943% of dry weight. They are micrograms per gram. The override is
  recorded in the provenance file rather than applied silently.
* **Per-sample microbiology columns are gone.** The previous file carried an APC
  and YMC value for every nutrient sample. Microbial counts come from OSD-780, a
  different study with different samples; they were never per-sample measurements
  of these plants.
* **OSD-655 is mizuna** (*Brassica rapa* var. *japonica*). Its OSDR study
  record describes VEG-04A/B as "two flight tests ... growing mizuna mustard".
  A 13 Oct 2026 revision relabelled it Tokyo Bekana without a source; reverted
  14 Oct 2026.

Usage:
    python3 data/fetch_osdr_data.py
    python3 data/fetch_osdr_data.py --dry-run

Requires pandas; downloads use the standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FILES_API = "https://visualization.osdr.nasa.gov/biodata/api/v2/dataset/{osd}/files/"
META_API = "https://visualization.osdr.nasa.gov/biodata/api/v2/dataset/{osd}/"
UA = "OSDR-Veggie-Nutrition-Dashboard/2.0"
THROTTLE_S = 2.0            # OSDR returns 502/503 without pacing
TIMEOUT_S = 120

METADATA_STUDIES = ["OSD-745", "OSD-655", "OSD-780"]

# OSD-780 is the microbial food-safety study for the VEG-04 (mizuna)
# missions. It is fetched as its own table rather than as columns on the
# nutrient rows, because it is not a per-sample measurement of those rows:
#
#   * It covers VEG04A and VEG04B only. There is no microbiology for lettuce
#     (OSD-745) at all, so any lettuce APC/YMC value is necessarily invented.
#   * Only 11 of the 37 OSD-655 nutrient samples share a base sample name with
#     it; 185 of its base names have no nutrient counterpart.
#   * It samples substrates the nutrient study does not: soil, wick, root,
#     water and hardware swabs as well as leaf. Pooling those with leaf would
#     misstate the food-safety question, which is about edible tissue.
#   * Leaf samples carry a sanitisation treatment (clean / unclean) and, on
#     VEG04B, up to three sequential harvests, so one plant maps to several
#     microbiology rows.
#
# The superseded literal data asserted one APC and one YMC value for every
# nutrient sample in both crops. None of that was measured.
MICROBIOLOGY = {
    "osd": "OSD-780",
    "assays": {
        "apc": ("Aerobic_Plate_Count", "TRANSFORMED"),
        "ymc": ("Yeast_Mold_Plate_Count", "Transformed"),
    },
    # Two value columns, used for different sample types and NOT interchangeable.
    # Tissue and substrate samples are homogenised and reported per gram fresh
    # weight. Hardware swabs and water samples have no fresh weight, so they are
    # reported per swab. Reading only the per-gram column silently discards the
    # 32 swab and 8 water rows; pooling the two would compare different units.
    "value_columns": {
        "colony_forming_unit_per_gram_fresh_weight_per_swab":
            "cfu_per_gram_fresh_weight",
        "colony_forming_units_per_swab": "cfu_per_swab",
    },
}

# VEG04A_GC_leaf_pillow3_red_clean / VEG04B_F_leaf_pillow7_blue_red_harvest2 /
# VEG04A_GC_soil_1_pillow3_red / VEG04A_F_Swab_Sample2_blue / VEG04A_F_water_preOp_1
RE_780 = re.compile(
    r"^(?P<mission>VEG04[AB])_(?P<cond>GC|F)_(?P<rest>.+)$", re.IGNORECASE)

STUDIES = {
    "745": {
        "osd": "OSD-745", "crop": "lettuce", "species": "Lactuca sativa",
        "cultivar": "Outredgeous", "reference": "Khodadad et al. 2020",
        "assays": {
            "elemental": ("ICPOESpectroscopy", "TRANSFORMED"),
            "orac": ("Oxygen Radical Absorbance Capacity", "TRANSFORMED"),
            "phenolics": ("Phenolic_Content", "TRANSFORMED"),
            "anthocyanins": ("Anthocyanin Content", "TRANSFORMED"),
        },
    },
    "655": {
        "osd": "OSD-655", "crop": "mizuna", "species": "Brassica rapa",
        "cultivar": "Mizuna", "reference": "Bunchek et al. 2024",
        "assays": {
            "elemental": ("ICPOES", "TRANSFORMED"),
            "orac": ("Oxygen Radical Absorbance Capacity", "TRANSFORMED"),
            "phenolics": ("Phenolic_Content", "TRANSFORMED"),
        },
    },
}

ELEMENTS = ["boron", "calcium", "copper", "iron", "magnesium", "manganese",
            "phosphorus", "potassium", "sodium", "sulfur", "zinc", "aluminium"]

SYMBOL = {"boron": "B", "calcium": "Ca", "copper": "Cu", "iron": "Fe",
          "magnesium": "Mg", "manganese": "Mn", "phosphorus": "P",
          "potassium": "K", "sodium": "Na", "sulfur": "S", "zinc": "Zn",
          "aluminium": "Al"}

# Source unit -> factor converting to micrograms per gram of dry weight.
UNIT_TO_UGG = {
    "microgram_per_gram": 1.0,
    "milligram_per_kilogram": 1.0,     # numerically identical to ug/g
    "milligram_per_gram": 1000.0,      # a genuine mg/g value would scale by 1000
}

# Columns whose stated unit is wrong in the archive, applied instead of the
# stated unit and reported in the provenance file.
UNIT_OVERRIDES = {
    ("OSD-655", element): "microgram_per_gram"
    for element in ("calcium", "potassium", "magnesium", "phosphorus", "sulfur")
}
OVERRIDE_EVIDENCE = (
    "Stated milligram_per_gram_of_dry_weight. Read as mg/g, mean potassium is "
    "2,943% of dry weight, calcium 651% and magnesium 805% -- physically "
    "impossible. Read as ug/g every value lands in the normal range for leafy "
    "Brassica tissue and agrees with the independently-scaled OSD-745 lettuce "
    "measurements. The archived data dictionary repeats the same wrong unit. "
    "Reported to OSDR; see SpaceMineralAtlas/fair/osdr_curation_report.md."
)

RE_745 = re.compile(r"^(VEG-\d+[AB])_([A-Z])_(Flight|Ground)_(\d+)days$")
RE_655 = re.compile(r"^(VEG04[AB])_(GC|F)_leaf_pillow(\d+)_(red|blue)$")


def mission_label(raw: str) -> str:
    """OSD-655/780 sample names write VEG04A; OSD-745 and the rest of the repo use VEG-04A."""
    return re.sub(r"^VEG(\d)", r"VEG-\1", raw.upper())


def _get(url: str, what: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            if resp.status != 200:
                raise SystemExit(f"FATAL: {what}: HTTP {resp.status}")
            return resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise SystemExit(f"FATAL: {what}: {type(exc).__name__} {exc}")


def fetch_study_metadata(osd: str, raw_dir: Path) -> None:
    """Save the study's OSDR metadata record, as the previous version did."""
    blob = _get(META_API.format(osd=osd), f"{osd} metadata")
    out = raw_dir / f"{osd.lower()}_osdr_metadata.json"
    out.write_bytes(blob)
    logger.info("%s: metadata saved (%d bytes)", osd, len(blob))
    time.sleep(THROTTLE_S)


def list_files(osd: str) -> dict:
    payload = json.loads(_get(FILES_API.format(osd=osd), f"{osd} file listing"))
    try:
        return payload[osd]["files"]
    except (KeyError, TypeError):
        raise SystemExit(f"FATAL: {osd}: unexpected file-listing shape")


def pick(files: dict, fragments: tuple[str, ...], osd: str, assay: str) -> str:
    matches = [n for n in files
               if n.lower().endswith(".csv")
               and all(f.lower() in n.lower() for f in fragments)]
    if not matches:
        raise SystemExit(f"FATAL: {osd}/{assay}: no archive file matching {fragments}")
    # Shortest name is the curated per-study product rather than a per-mission
    # export that happens to share the same fragments.
    return sorted(matches, key=len)[0]


def download(files: dict, name: str, osd: str) -> bytes:
    rec = files[name]
    # The datamanager URL serves the bytes. The biodata REST_URL serves a JSON
    # metadata record describing the file; asking it for data yields a
    # plausible-looking file that is not data.
    for key in ("URL", "REST_URL"):
        url = rec.get(key)
        if not url:
            continue
        blob = _get(url, f"{osd}/{name}")
        head = blob[:2048].lstrip()
        if head.startswith(b"{") or head.startswith(b"["):
            logger.warning("%s served JSON metadata rather than data; trying next", key)
            continue
        if b"," not in blob[:2048]:
            raise SystemExit(f"FATAL: {osd}/{name}: no delimiter found; not a CSV")
        return blob
    raise SystemExit(f"FATAL: {osd}/{name}: no endpoint returned file contents")


def parse_elemental(frame: pd.DataFrame, osd: str) -> tuple[pd.DataFrame, list[dict]]:
    """Return (sample x element in ug/g, unit provenance)."""
    out = pd.DataFrame({"sample_name": frame[frame.columns[0]].astype(str).str.strip()})
    provenance = []
    for column in frame.columns[1:]:
        match = re.match(r"^([a-z]+)_((?:micro|milli)gram_per_(?:gram|kilogram))", column)
        if not match or match.group(1) not in ELEMENTS:
            continue
        element, stated = match.group(1), match.group(2)
        effective = UNIT_OVERRIDES.get((osd, element), stated)
        factor = UNIT_TO_UGG[effective]
        out[element] = pd.to_numeric(frame[column], errors="coerce") * factor
        provenance.append({
            "study": osd, "element": element, "source_column": column,
            "stated_unit": stated, "unit_used": effective,
            "override_applied": effective != stated, "factor_to_ugg": factor,
            "evidence": OVERRIDE_EVIDENCE if effective != stated
                        else "stated unit used as given",
        })
    if not provenance:
        raise SystemExit(f"FATAL: {osd}: no element columns recognised")
    return out, provenance


def parse_single_value(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "sample_name": frame[frame.columns[0]].astype(str).str.strip(),
        name: pd.to_numeric(frame[frame.columns[1]], errors="coerce"),
    })
    return out[out["sample_name"].ne("") & out["sample_name"].ne("nan")]


def sample_metadata(sample: str, suffix: str, spec: dict) -> dict | None:
    if suffix == "745":
        m = RE_745.match(sample)
        if not m:
            return None
        return {"Sample Name": sample, "Mission": m.group(1),
                "Spaceflight/Ground Control": m.group(3),
                "Plant Number": m.group(2), "Harvest Day": int(m.group(4)),
                "Crop": spec["crop"], "Light": ""}
    m = RE_655.match(sample)
    if not m:
        return None
    return {"Sample Name": sample, "Mission": mission_label(m.group(1)),
            "Spaceflight/Ground Control": "Ground" if m.group(2) == "GC" else "Flight",
            "Plant Number": f"pillow{m.group(3)}", "Harvest Day": "",
            "Crop": spec["crop"], "Light": m.group(4)}


def build(suffix: str, spec: dict, raw_dir: Path, dry_run: bool) -> dict:
    osd = spec["osd"]
    files = list_files(osd)
    chosen = {assay: pick(files, frags, osd, assay)
              for assay, frags in spec["assays"].items()}

    logger.info("%s (%s): %d files listed; selected:", osd, spec["crop"], len(files))
    for assay, name in chosen.items():
        logger.info("    %-13s %s", assay, name)
    if dry_run:
        return {"study": osd, "files": chosen, "dry_run": True}

    tables, checksums = {}, []
    for assay, name in chosen.items():
        blob = download(files, name, osd)
        (raw_dir / name.replace("/", "_")).write_bytes(blob)
        checksums.append({"file": name, "bytes": len(blob),
                          "sha256": hashlib.sha256(blob).hexdigest()})
        tables[assay] = pd.read_csv(io.BytesIO(blob), encoding="utf-8-sig")
        time.sleep(THROTTLE_S)

    merged, unit_prov = parse_elemental(tables["elemental"], osd)
    for assay in ("orac", "phenolics", "anthocyanins"):
        if assay in tables:
            merged = merged.merge(parse_single_value(tables[assay], assay),
                                  on="sample_name", how="outer")

    rows = [sample_metadata(s, suffix, spec) for s in merged["sample_name"]]
    if any(r is None for r in rows):
        bad = [s for s, r in zip(merged["sample_name"], rows) if r is None]
        raise SystemExit(f"FATAL: {osd}: unparsed sample names {bad[:5]}")
    meta = pd.DataFrame(rows)

    # Nutrient table in the historical column shape; ug/g converted to mg/g.
    nutrients = pd.DataFrame({"Sample Name": merged["sample_name"]})
    for element in ELEMENTS:
        if element in merged.columns and merged[element].notna().any():
            nutrients[f"{SYMBOL[element]} (mg/g)"] = merged[element] / 1000.0
    for assay, label in (("phenolics", "Phenolics (GAE mg/g)"),
                         ("anthocyanins", "Anthocyanins (mg/g)"),
                         ("orac", "ORAC (umol TE/g)")):
        if assay in merged.columns:
            nutrients[label] = merged[assay]

    meta.to_csv(raw_dir / f"osd_{suffix}_metadata.csv", index=False)
    nutrients.to_csv(raw_dir / f"osd_{suffix}_nutrients.csv", index=False)

    measured = [c for c in nutrients.columns if c != "Sample Name"]
    absent = [SYMBOL[e] for e in ELEMENTS
              if e not in merged.columns or merged[e].isna().all()]
    counts = meta["Spaceflight/Ground Control"].value_counts().to_dict()

    # Assays do not cover identical sample sets, and the join across them is an
    # outer one: a sample measured by any assay gets a row. Reporting only the
    # row count would overstate how many samples have elemental data, so the
    # per-assay coverage is broken out and any sample lacking elemental values
    # is named rather than left for a reader to discover.
    element_columns = [c for c in nutrients.columns if c.endswith("(mg/g)")]
    has_elemental = nutrients[element_columns].notna().any(axis=1)
    coverage = {
        "n_rows_any_assay": int(len(nutrients)),
        "n_with_elemental": int(has_elemental.sum()),
        "samples_without_elemental":
            nutrients.loc[~has_elemental, "Sample Name"].tolist(),
        "n_by_assay": {
            label: int(nutrients[label].notna().sum())
            for label in measured if not label.endswith("(mg/g)")
        },
    }
    if coverage["samples_without_elemental"]:
        logger.info("  note: %d sample(s) measured by a non-elemental assay only: %s",
                    len(coverage["samples_without_elemental"]),
                    ", ".join(coverage["samples_without_elemental"]))
    logger.info("  -> %d rows (%s); %d with elemental data; %d measured columns; "
                "not measured: %s",
                len(nutrients), ", ".join(f"{k}={v}" for k, v in counts.items()),
                coverage["n_with_elemental"], len(measured),
                ", ".join(absent) or "none")

    return {
        "study": osd, "crop": spec["crop"], "species": spec["species"],
        "cultivar": spec["cultivar"], "reference": spec["reference"],
        "files": chosen, "checksums": checksums,
        "n_by_condition": counts, "coverage": coverage,
        "measured_columns": measured, "elements_not_measured": absent,
        "unit_provenance": unit_prov,
    }


def parse_microbiology_sample(sample: str) -> dict | None:
    """Decompose an OSD-780 sample name into its experimental factors.

    Returns None for a name that does not match, so an unparsed name becomes a
    hard failure rather than a silently mis-grouped row.
    """
    m = RE_780.match(sample.strip())
    if not m:
        return None
    rest = m.group("rest")
    tokens = rest.split("_")

    # Sample type: the material swabbed or homogenised.
    lowered = rest.lower()
    for token, kind in (("leaf", "leaf"), ("soil", "soil"), ("wick", "wick"),
                        ("root", "root"), ("water", "water"), ("swab", "swab")):
        if token in lowered:
            sample_type = kind
            break
    else:
        sample_type = "other"

    light = next((c for c in ("red", "blue") if c in lowered), "")
    treatment = ("clean" if "_clean" in lowered
                 else "unclean" if "unclean" in lowered else "")
    harvest = re.search(r"harvest(\d)", lowered)
    pillow = re.search(r"pillow(\d+)", lowered)

    return {
        "sample_name": sample.strip(),
        "mission": mission_label(m.group("mission")),
        "condition": "Ground" if m.group("cond").upper() == "GC" else "Flight",
        "sample_type": sample_type,
        "light": light,
        "sanitisation": treatment,
        "harvest": int(harvest.group(1)) if harvest else None,
        "pillow": int(pillow.group(1)) if pillow else None,
        "is_edible_tissue": sample_type == "leaf",
    }


def build_microbiology(raw_dir: Path, dry_run: bool) -> dict:
    """Fetch OSD-780 and emit a standalone microbiology table."""
    osd = MICROBIOLOGY["osd"]
    files = list_files(osd)
    chosen = {a: pick(files, f, osd, a) for a, f in MICROBIOLOGY["assays"].items()}
    logger.info("%s (microbiology): %d files listed; selected:", osd, len(files))
    for assay, name in chosen.items():
        logger.info("    %-5s %s", assay, name)
    if dry_run:
        return {"study": osd, "files": chosen, "dry_run": True}

    frames, checksums = {}, []
    value_columns = MICROBIOLOGY["value_columns"]
    for assay, name in chosen.items():
        blob = download(files, name, osd)
        (raw_dir / name.replace("/", "_")).write_bytes(blob)
        checksums.append({"file": name, "bytes": len(blob),
                          "sha256": hashlib.sha256(blob).hexdigest()})
        frame = pd.read_csv(io.BytesIO(blob), encoding="utf-8-sig")
        # The yeast/mould export's first header carries a literal newline.
        frame.columns = [c.strip() for c in frame.columns]
        for column in value_columns:
            if column not in frame.columns:
                raise SystemExit(f"FATAL: {osd}/{name}: missing column {column!r}")
        frames[assay] = frame
        time.sleep(THROTTLE_S)

    records = []
    for assay, frame in frames.items():
        for _, row in frame.iterrows():
            raw_name = str(row["Sample Name"]).strip()
            # Trailing blank rows are skipped. A name that is present but does
            # not parse is still fatal: silently mis-grouping a real sample is
            # the failure mode this guard exists for.
            if not raw_name or raw_name.lower() == "nan":
                continue
            parsed = parse_microbiology_sample(raw_name)
            if parsed is None:
                raise SystemExit(
                    f"FATAL: {osd}: unparsed sample name {raw_name!r}")
            values = {out: pd.to_numeric(row[src], errors="coerce")
                      for src, out in value_columns.items()}
            if all(pd.isna(v) for v in values.values()):
                continue
            # Record which basis this row is measured on, so the two are never
            # pooled: per gram of fresh tissue, or per hardware/water swab.
            basis = ("per_gram_fresh_weight"
                     if pd.notna(values["cfu_per_gram_fresh_weight"])
                     else "per_swab")
            records.append({
                **parsed, "assay": assay.upper(), "measurement_basis": basis,
                **{k: (float(v) if pd.notna(v) else None) for k, v in values.items()},
                "fresh_weight_gram": pd.to_numeric(
                    row.get("fresh_weight_gram"), errors="coerce"),
            })

    table = pd.DataFrame(records)
    if table.empty:
        raise SystemExit(f"FATAL: {osd}: no usable microbiology rows")
    out = raw_dir.parent / "processed" / "microbiology_osd780.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)

    leaf = table[table["is_edible_tissue"]]
    logger.info("  -> %d rows (%d leaf); types: %s; missions: %s; bases: %s",
                len(table), len(leaf),
                ", ".join(sorted(table["sample_type"].unique())),
                ", ".join(sorted(table["mission"].unique())),
                ", ".join(f"{k}={v}" for k, v in
                          table["measurement_basis"].value_counts().items()))

    # How far this can be joined to the nutrient cohort, stated rather than assumed.
    try:
        nutrient = set(pd.read_csv(raw_dir / "osd_655_nutrients.csv")["Sample Name"])
    except FileNotFoundError:
        nutrient = set()
    base = {re.sub(r"_(clean|unclean)(_harvest\d)?$", "", s)
            for s in leaf["sample_name"]}
    overlap = sorted(nutrient & base)

    return {
        "study": osd, "files": chosen, "checksums": checksums,
        "n_rows": int(len(table)), "n_leaf_rows": int(len(leaf)),
        "value_units": {
            "cfu_per_gram_fresh_weight": "tissue and substrate samples",
            "cfu_per_swab": "hardware swab and water samples (no fresh weight)",
        },
        "n_by_measurement_basis": table["measurement_basis"].value_counts().to_dict(),
        "n_by_assay": table["assay"].value_counts().to_dict(),
        "n_by_sample_type": table["sample_type"].value_counts().to_dict(),
        "missions": sorted(table["mission"].unique()),
        "covers_lettuce": False,
        "join_to_nutrients": {
            "note": ("Not a per-sample join. Reported so the partial overlap is "
                     "visible rather than assumed."),
            "n_nutrient_samples": len(nutrient),
            "n_matching_by_base_name": len(overlap),
            "matching": overlap,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch real NASA OSDR Veggie data.")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve filenames and exit without downloading")
    args = parser.parse_args()

    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not args.dry_run:
        for osd in METADATA_STUDIES:
            fetch_study_metadata(osd, raw_dir)

    report = [build(suffix, spec, raw_dir, args.dry_run)
              for suffix, spec in STUDIES.items()]
    micro = build_microbiology(raw_dir, args.dry_run)
    if args.dry_run:
        print("\n--dry-run: nothing downloaded.")
        return 0

    (raw_dir / "osdr_fetch_provenance.json").write_text(json.dumps({
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "script": "data/fetch_osdr_data.py",
        "note": ("Values are read from the NASA OSDR archive. This replaces a "
                 "version that emitted literals. No synthetic fallback exists."),
        "studies": report,
        "microbiology": micro,
    }, indent=2) + "\n")
    logger.info("wrote data/raw/osdr_fetch_provenance.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
