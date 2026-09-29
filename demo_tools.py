"""Demo function tools for field-service voice agents."""

from __future__ import annotations

import os

from agents import function_tool
from demo_catalog import (
    SERVICE_CASES,
    TROUBLESHOOTING_STEPS,
    build_devices,
    normalize_case_id,
    normalize_product_line,
    normalize_serial,
    requires_immediate_escalation,
)
from dotenv import load_dotenv

load_dotenv()

DEMO_SITE_NAME = os.environ.get("DEMO_SITE_NAME", "Memorial Hospital")
DEVICES = build_devices(DEMO_SITE_NAME)


@function_tool
def lookup_device(serial_number: str) -> str:
    """Look up a capital equipment device by serial number (demo sample data)."""
    serial = normalize_serial(serial_number)
    device = DEVICES.get(serial)
    if device is None:
        return (
            f"No device found for serial {serial_number!r}. "
            "Verify the asset label or open a new service case with your FSE team."
        )
    cases = ", ".join(device["linked_cases"]) if device["linked_cases"] else "none open"
    return (
        f"Serial {serial}: {device['product_line']} at {device['site']}. "
        f"Warranty: {device['warranty_status']}. "
        f"Status: {device['operational_status']}. "
        f"Linked cases: {cases}."
    )


@function_tool
def get_service_case(case_id: str) -> str:
    """Get status and notes for a service case by case ID (demo sample data)."""
    case_key = normalize_case_id(case_id)
    case = SERVICE_CASES.get(case_key)
    if case is None:
        return (
            f"No case found for {case_id!r}. "
            "Check the case number or contact dispatch to create a new ticket."
        )
    return (
        f"{case_key} for {case['product_line']} (serial {case['serial_number']}): "
        f"Status {case['status']}. ETA {case['eta']}. "
        f"Assigned FSE: {case['assigned_fse']}. "
        f"Latest note: {case['last_note']}"
    )


@function_tool
def get_troubleshooting_guide(product_line: str, symptom: str) -> str:
    """Return a ordered non-invasive troubleshooting checklist for a product line and symptom."""
    if requires_immediate_escalation(symptom):
        return (
            "Stop use of the equipment immediately. Do not attempt further troubleshooting. "
            "Escalate to field service and follow your site’s safety and IFU procedures. "
            "This demo assistant cannot authorize return to service."
        )
    product = normalize_product_line(product_line)
    steps = TROUBLESHOOTING_STEPS.get(product)
    if steps is None:
        return (
            f"No demo checklist for product line {product_line!r}. "
            "Try Visualization System, Power Console, or Navigation Hub, or escalate to FSE."
        )
    numbered = "; ".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    return f"Symptom noted: {symptom}. Checklist for {product}: {numbered}"
