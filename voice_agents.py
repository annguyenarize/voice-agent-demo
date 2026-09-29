"""Multi-agent Realtime graph: supervisor + specialists with scoped tools."""

from __future__ import annotations

from agents.realtime import RealtimeAgent
from agents.realtime.handoffs import realtime_handoff
from demo_tools import get_service_case, get_troubleshooting_guide, lookup_device

SAFETY_NOTE = (
    "Demo sample data only — not for patient care or clinical advice. "
    "For production incidents follow official IFU and service procedures."
)

RETURN_TO_SUPERVISOR = (
    "Return to the Service Supervisor after you finish helping, or immediately if the "
    "user's request is outside your specialty. The supervisor triages every new user turn."
)

SPECIALIST_WORKFLOW = (
    "When you receive a handoff for your specialty: (1) call your tool immediately, "
    "(2) speak the full tool result to the user in audio — never skip this step. "
    "Do not call return_to_supervisor; the session returns to the supervisor automatically "
    "after you finish speaking. "
    "Speak as one field-service assistant: do not mention routing, handoffs, supervisors, "
    "specialists, or internal agent names. Do not greet or say you were connected. "
    "Start with the factual answer. "
    "If you are active but the user's latest request is outside your specialty "
    "(e.g. serial lookup while you are the case agent), call return_to_supervisor immediately "
    "without using your tool and without spoken preamble."
)

SUPERVISOR_ROUTING = (
    "You route requests silently in the background. For device, case, or troubleshooting "
    "requests you must invoke the matching handoff tool with NO spoken output—no words, "
    "no greetings, no mention of routing, transfers, or other agents. "
    "The user should only hear the specialist's answer after you hand off. "
    "Never answer device, case, or troubleshooting questions yourself. "
    "When waiting after a specialist finishes, stay silent until the user speaks again, "
    "then hand off again with zero speech. "
    "Only speak aloud for immediate safety issues (stop use, escalate to a human FSE)."
)


def build_agent_graph() -> RealtimeAgent:
    device_agent = RealtimeAgent(
        name="Device Registry Agent",
        instructions=(
            f"{SPECIALIST_WORKFLOW} "
            "You look up hospital capital equipment by serial number using lookup_device only. "
            "Never invent device records. Speak briefly and professionally. "
            "If the serial is unclear, ask the user to repeat it."
        ),
        tools=[lookup_device],
        handoffs=[],
    )

    case_agent = RealtimeAgent(
        name="Case Status Agent",
        instructions=(
            f"{SPECIALIST_WORKFLOW} "
            "You provide service case status and notes using get_service_case only. "
            "Never invent case details. Speak briefly and professionally. "
            "If the case ID is unclear, ask the user to repeat it."
        ),
        tools=[get_service_case],
        handoffs=[],
    )

    troubleshooting_agent = RealtimeAgent(
        name="Troubleshooting Agent",
        instructions=(
            f"{SPECIALIST_WORKFLOW} "
            "You provide non-invasive troubleshooting checklists using get_troubleshooting_guide only. "
            "Never invent repair steps or parts availability. Speak briefly and professionally. "
            "If the user describes patient harm, sterilization failure, safety interlock faults, fire, "
            "smoke, or electrical shock, tell them to stop use and escalate — do not troubleshoot further."
        ),
        tools=[get_troubleshooting_guide],
        handoffs=[],
    )

    supervisor = RealtimeAgent(
        name="Service Supervisor",
        instructions=(
            f"{SUPERVISOR_ROUTING} "
            "Routing map (handoff tools only, never say these names aloud): "
            "serial or asset lookup → device handoff; "
            "case ID or ticket status → case handoff; "
            "symptoms or troubleshooting checklist → troubleshooting handoff."
        ),
        tools=[],
        handoffs=[
            realtime_handoff(
                device_agent,
                tool_description_override=(
                    "Silent route: user needs device or asset lookup by serial number."
                ),
            ),
            realtime_handoff(
                case_agent,
                tool_description_override=(
                    "Silent route: user asks about a service case ID, ticket status, or dispatch note."
                ),
            ),
            realtime_handoff(
                troubleshooting_agent,
                tool_description_override=(
                    "Silent route: user describes equipment symptoms or wants a troubleshooting checklist."
                ),
            ),
        ],
    )

    device_agent.handoffs = [
        realtime_handoff(
            supervisor,
            tool_name_override="return_to_supervisor",
            tool_description_override=RETURN_TO_SUPERVISOR,
        )
    ]
    case_agent.handoffs = [
        realtime_handoff(
            supervisor,
            tool_name_override="return_to_supervisor",
            tool_description_override=RETURN_TO_SUPERVISOR,
        )
    ]
    troubleshooting_agent.handoffs = [
        realtime_handoff(
            supervisor,
            tool_name_override="return_to_supervisor",
            tool_description_override=RETURN_TO_SUPERVISOR,
        )
    ]

    return supervisor
