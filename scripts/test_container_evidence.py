"""Offline schema checks with valid and invalid component/license data."""

import importlib.util
import unittest
from pathlib import Path

from jsonschema import ValidationError

SCRIPT = Path(__file__).with_name("record_container_evidence.py")
SPEC = importlib.util.spec_from_file_location("container_evidence", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SCHEMAS = SCRIPT.parent.parent / "schemas/cyclonedx-1.6"


class ContainerEvidenceTests(unittest.TestCase):
    def test_valid_component_and_spdx_license(self):
        module.validate_sbom(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "version": 1,
                "components": [
                    {
                        "type": "library",
                        "name": "example",
                        "licenses": [{"license": {"id": "MIT"}}],
                    }
                ],
            },
            SCHEMAS,
        )

    def test_current_spdx_identifier_is_retained(self):
        module.validate_sbom(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "version": 1,
                "components": [
                    {
                        "type": "library",
                        "name": "example",
                        "licenses": [{"license": {"id": "SMAIL-GPL"}}],
                    }
                ],
            },
            SCHEMAS,
        )

    def test_invalid_license_is_rejected(self):
        with self.assertRaises(ValidationError):
            module.validate_sbom(
                {
                    "bomFormat": "CycloneDX",
                    "specVersion": "1.6",
                    "version": 1,
                    "components": [
                        {
                            "type": "library",
                            "name": "example",
                            "licenses": [{"license": {"id": 123}}],
                        }
                    ],
                },
                SCHEMAS,
            )

    def test_empty_inventory_is_rejected(self):
        with self.assertRaises(ValueError):
            module.validate_sbom(
                {"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []},
                SCHEMAS,
            )


if __name__ == "__main__":
    unittest.main()
