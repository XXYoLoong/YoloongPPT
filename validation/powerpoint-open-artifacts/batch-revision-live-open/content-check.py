"""Compare saved, actual PowerPoint COM readings with each product DeckSpec.

This does not launch Office or edit a deck. Embedded image hashes are separate
OOXML evidence; they are not claimed as pixel data read through COM.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\x0b", "\n")


def image_parts(archive: zipfile.ZipFile, index: int) -> dict:
    slide_path = f"ppt/slides/slide{index}.xml"
    slide = ET.fromstring(archive.read(slide_path))
    rels = ET.fromstring(archive.read(f"ppt/slides/_rels/slide{index}.xml.rels"))
    targets = {rel.get("Id"): rel.get("Target") for rel in rels}
    result = {}
    for picture in slide.findall(".//p:pic", NS):
        props = picture.find("p:nvPicPr/p:cNvPr", NS)
        blip = picture.find("p:blipFill/a:blip", NS)
        target = targets[blip.get(f"{{{NS['r']}}}embed")]
        part = posixpath.normpath(posixpath.join("ppt/slides", target))
        result[props.get("name")] = {
            "part": part,
            "sha256": hashlib.sha256(archive.read(part)).hexdigest(),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("content-check.json"))
    args = parser.parse_args()
    report_path = Path(__file__).with_name("report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    checks = []
    runs = []

    def record(run: str, kind: str, slide: int | None, name: str | None, expected, actual) -> None:
        checks.append({"run_id": run, "kind": kind, "slide": slide, "object_name": name,
                       "expected": expected, "actual": actual, "passed": expected == actual})

    for source in report["inputs"]:
        path = Path(source["path"])
        spec_path = path.with_name("deck-spec.json")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        snapshot = source["snapshot"]
        run = source["source_run_id"]
        record(run, "source_hash_after_COM", None, None, source["sha256_before"], sha256(path))
        record(run, "COM_read_only", None, None, True, source["read_only_actual"])
        record(run, "page_count", None, None, len(spec["slides"]), snapshot["slide_count"])
        native_types = Counter(obj["type_name"] for page in snapshot["slides"] for obj in page["shapes"])
        runs.append({"run_id": run, "path": str(path), "pptx_sha256": sha256(path),
                     "deck_spec_sha256": sha256(spec_path), "slides": snapshot["slide_count"],
                     "shapes": sum(len(page["shapes"]) for page in snapshot["slides"]),
                     "native_type_counts": dict(native_types)})
        with zipfile.ZipFile(path) as archive:
            for index, page in enumerate(spec["slides"], 1):
                actual = snapshot["slides"][index - 1]
                by_name = {obj["name"]: obj for obj in actual["shapes"]}
                record(run, "object_count", index, None, len(page["elements"]), len(actual["shapes"]))
                embedded = image_parts(archive, index)
                for element in page["elements"]:
                    name = element["object_id"]
                    shape = by_name.get(name)
                    record(run, "native_object_exists", index, name, True, shape is not None)
                    if shape is None:
                        continue
                    expected = [float(n) * 72 for n in element["bounds"]]
                    geometry_basis = "bounds"
                    if element["type"] == "connector":
                        # writer.connector_shape consumes the explicit start/end
                        # endpoints, while layout bounds use a 0.001-inch minimum
                        # height for the horizontal line. COM exposes zero height.
                        start, end = element["data"]["start"], element["data"]["end"]
                        expected = [min(start[0], end[0]) * 72, min(start[1], end[1]) * 72,
                                    abs(end[0] - start[0]) * 72, abs(end[1] - start[1]) * 72]
                        geometry_basis = "explicit_connector_endpoints"
                    measured = [shape[key] for key in ["left_pt", "top_pt", "width_pt", "height_pt"]]
                    # Office exposes Single precision coordinates. 0.001 pt is
                    # a measurement tolerance, not a layout/QA acceptance rule.
                    record(run, "COM_geometry_within_0.001pt", index, name, True,
                           all(abs(a - b) <= 0.001 for a, b in zip(expected, measured)))
                    checks[-1]["measurement"] = {
                        "geometry_basis": geometry_basis, "spec_bounds_inches": element["bounds"],
                        "expected_pt": expected, "actual_pt": measured, "threshold_pt": 0.001,
                    }
                    if element["type"] == "text":
                        record(run, "native_textframe", index, name, True, shape["has_text_frame"])
                        expected_text = normalized_text("\n".join(element["text"]))
                        actual_text = normalized_text(shape["text"]["content"])
                        record(run, "title_text" if element["role"] == "title" else "text_content",
                               index, name, expected_text, actual_text)
                    elif element["type"] == "image":
                        record(run, "COM_picture_type", index, name, "Picture", shape["type_name"])
                        record(run, "OOXML_embedded_image_sha256", index, name,
                               element["data"]["sha256"], embedded.get(name, {}).get("sha256"))
                    elif element["type"] == "chart":
                        record(run, "COM_native_chart", index, name, True, shape["has_chart"])
                        expected_data = element["data"]
                        series = shape["chart"]["series"]
                        record(run, "COM_chart_series_count", index, name,
                               len(expected_data["series"]), len(series))
                        for expected_series, actual_series in zip(expected_data["series"], series):
                            record(run, "COM_chart_series_name", index, name,
                                   expected_series["name"], actual_series["name"])
                            record(run, "COM_chart_values", index, name,
                                   expected_series["values"], actual_series["values"])
                            record(run, "COM_chart_categories", index, name,
                                   expected_data["categories"], actual_series["categories"])

    failed = [check for check in checks if not check["passed"]]
    result = {
        "status": "passed_bounded_content_check" if not failed else "failed",
        "requirement_ids": report["requirement_ids"], "source_COM_report_sha256": sha256(report_path),
        "check_script_sha256": sha256(Path(__file__)), "runs": runs,
        "check_count": len(checks), "failed_count": len(failed), "checks": checks,
        "boundary": "Actual native PowerPoint COM text/chart/shape readings compared to final product DeckSpec. Image bytes are separately verified in OOXML. No source edit, visual rendering, new editability mutation, repair-dialog observation, full preservation or complete AC-028 acceptance.",
        "ac028_passed": False,
    }
    if args.output.resolve().drive.upper() == "C:":
        raise ValueError("Project evidence must not be written to C:")
    if args.output.exists():
        raise FileExistsError(f"Use a new output name to preserve evidence: {args.output}")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks), "failed_count": len(failed),
                      "failures": failed, "output": str(args.output)}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
