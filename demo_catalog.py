"""Demo medical device service catalog"""

from __future__ import annotations

import re
from typing import TypedDict

DEFAULT_DEMO_SITE_NAME = "Memorial Hospital"

SERIAL_PREFIX = "MDV"


class DeviceRecord(TypedDict):
    product_line: str
    site: str
    warranty_status: str
    operational_status: str
    linked_cases: list[str]


class CaseRecord(TypedDict):
    serial_number: str
    product_line: str
    status: str
    eta: str
    assigned_fse: str
    last_note: str


SERVICE_CASES: dict[str, CaseRecord] = {
    "CASE-10482": {
        "serial_number": "MDV-7842-019",
        "product_line": "Visualization System",
        "status": "Awaiting parts",
        "eta": "2026-09-28",
        "assigned_fse": "Jordan Lee",
        "last_note": "Display flicker on cold boot; backlight module ordered.",
    },
    "CASE-10491": {
        "serial_number": "MDV-2201-441",
        "product_line": "Power Console",
        "status": "In progress",
        "eta": "2026-09-24",
        "assigned_fse": "Sam Rivera",
        "last_note": "Intermittent foot-pedal latency; firmware diagnostic scheduled.",
    },
}

PRODUCT_ALIASES: dict[str, str] = {
    "visualization system": "Visualization System",
    "visualization": "Visualization System",
    "surgical visualization tower": "Visualization System",
    "power console": "Power Console",
    "powered instrument console": "Power Console",
    "navigation hub": "Navigation Hub",
}

TROUBLESHOOTING_STEPS: dict[str, list[str]] = {
    "Visualization System": [
        "Confirm the system is on a dedicated hospital-grade power outlet.",
        "Reseat display and tower data cables; check for bent pins.",
        "Power-cycle the tower, wait 60 seconds, and note if flicker persists on boot.",
        "Check room lighting settings — auto-brightness can mimic display instability.",
        "If flicker continues or worsens, stop clinical use and escalate to field service.",
    ],
    "Power Console": [
        "Verify foot pedal and handpiece connections are fully seated.",
        "Inspect cables for damage; swap with a known-good pedal if available.",
        "Run the onboard connection test from the service menu.",
        "Confirm firmware is on the approved version for this site.",
        "If latency or unexpected stops continue, quarantine the console and escalate.",
    ],
    "Navigation Hub": [
        "Confirm network link and time sync to the facility NTP source.",
        "Restart the hub and verify calibration status in the service dashboard.",
        "Check that tracking markers are clean and within line of sight.",
        "If registration drifts repeatedly, escalate to field service.",
    ],
}

ESCALATION_SYMPTOM_KEYWORDS = (
    "patient harm",
    "injury",
    "sterilization",
    "safety interlock",
    "fire",
    "smoke",
    "electrical shock",
)


def build_devices(demo_site_name: str = DEFAULT_DEMO_SITE_NAME) -> dict[str, DeviceRecord]:
    return {
        "MDV-7842-019": {
            "product_line": "Visualization System",
            "site": demo_site_name,
            "warranty_status": "Active service contract",
            "operational_status": "Degraded — open service case",
            "linked_cases": ["CASE-10482"],
        },
        "MDV-2201-441": {
            "product_line": "Power Console",
            "site": demo_site_name,
            "warranty_status": "Active service contract",
            "operational_status": "In service — maintenance visit scheduled",
            "linked_cases": ["CASE-10491"],
        },
        "MDV-9910-002": {
            "product_line": "Navigation Hub",
            "site": "Riverside Demo Clinic",
            "warranty_status": "Contract renewal pending",
            "operational_status": "Operational",
            "linked_cases": [],
        },
    }


def normalize_serial(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    match = re.match(rf"^{SERIAL_PREFIX}(\d{{4}})(\d{{3}})$", cleaned)
    if match:
        return f"{SERIAL_PREFIX}-{match.group(1)}-{match.group(2)}"
    return raw.strip().upper()


def normalize_case_id(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    if cleaned.isdigit():
        return f"CASE-{cleaned}"
    if cleaned.startswith("CASE") and not cleaned.startswith("CASE-"):
        digits = cleaned[4:]
        if digits.isdigit():
            return f"CASE-{digits}"
    return raw.strip().upper()


def normalize_product_line(raw: str) -> str:
    key = raw.strip().lower()
    return PRODUCT_ALIASES.get(key, raw.strip())


def requires_immediate_escalation(symptom: str) -> bool:
    lower = symptom.lower()
    return any(kw in lower for kw in ESCALATION_SYMPTOM_KEYWORDS)
