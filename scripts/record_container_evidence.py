"""Validate an image SBOM and bind it to the inspected image and source commit."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource


def validate_sbom(bom, schemas):
    documents = [
        json.loads(p.read_text(encoding="utf-8-sig"))
        for p in schemas.glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (d["$id"], Resource.from_contents(d)) for d in documents
    )
    schema = next(d for d in documents if d["$id"].endswith("bom-1.6.schema.json"))
    Draft7Validator(schema, registry=registry).validate(bom)
    if bom.get("specVersion") != "1.6" or not bom.get("components"):
        raise ValueError("Expected a non-empty CycloneDX 1.6 SBOM")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--component", choices=["frontend", "backend"], required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--registry-ref")
    args = parser.parse_args()
    directory = args.directory
    bom = json.loads((directory / "image.cdx.json").read_text())
    native = json.loads((directory / "image.syft.json").read_text())
    image = json.loads((directory / "image-inspect.json").read_text())[0]
    validate_sbom(bom, Path(__file__).resolve().parents[1] / "schemas/cyclonedx-1.6")
    if native["source"]["metadata"]["imageID"] != image["Id"]:
        raise ValueError("SBOM source image ID does not match Docker inspect")
    if image["Config"]["Labels"]["org.opencontainers.image.revision"] != args.commit:
        raise ValueError("Image revision does not match the source commit")
    if not image["Config"].get("User") or image["Config"]["User"] in ["root", "0"]:
        raise ValueError("Image must declare a non-root runtime user")
    packages = {}
    for component in bom["components"]:
        packages.setdefault(component["name"].lower(), []).append(
            component.get("version")
        )
    names = (
        ["django", "daphne", "urllib3", "proxmoxer"]
        if args.component == "backend"
        else ["nginx", "vue", "axios", "vitest"]
    )
    if args.component == "backend" and not all(name in packages for name in names):
        raise ValueError("Expected Python packages missing from backend SBOM")
    result = {
        "component": args.component,
        "commit": args.commit,
        "run_url": args.run_url,
        "recorded_at": datetime.now(UTC).isoformat(),
        "image_id": image["Id"],
        "registry_ref": args.registry_ref,
        "runtime_user": image["Config"]["User"],
        "platform": image["Os"] + "/" + image["Architecture"],
        "syft_version": native["descriptor"]["version"],
        "cyclonedx_schema_valid": True,
        "schema_source_commit": "55343ba19dee1785acf1ce9191540d5fd7b590db",
        "component_count": len(bom["components"]),
        "dependency_entries": len(bom.get("dependencies", [])),
        "components_without_license": sum(
            not c.get("licenses") for c in bom["components"]
        ),
        "sampled_packages": {name: packages.get(name, []) for name in names},
        "license_compliance_assessed": False,
        "vulnerability_scan_performed": False,
        "files": {},
    }
    for name in [
        "image.cdx.json",
        "image.syft.json",
        "image-inspect.json",
        "image.tar",
    ]:
        path = directory / name
        if path.exists():
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            result["files"][name] = {
                "sha256": digest.hexdigest(),
                "bytes": path.stat().st_size,
            }
    (directory / "evidence.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(  # noqa: T201 - concise command-line evidence summary
        json.dumps(
            {
                k: result[k]
                for k in [
                    "component",
                    "image_id",
                    "registry_ref",
                    "component_count",
                    "sampled_packages",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
