"""Negotiator — per-user state machine for the agent-to-agent protocol.

LLM-free. Drives the protocol slice-by-slice; later slices add BATCH_SCHEDULE,
FREE_BUSY, PROPOSE, etc. on top of the HELLO scaffolding here.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from agent_scheduling.adapters.base import (
    EmailCalendarAdapter,
    Event,
    InviteResult,
    MeetingInvite,
    TimeWindow,
)
from agent_scheduling.privacy import PrivacyPolicyStore, apply_filter
from agent_scheduling.protocol import Envelope, MessageType
from agent_scheduling.solver import MeetingRequest, ProposedMeeting


def _event_to_dict(event: Event) -> dict:
    return {
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "attendees": list(event.attendees),
        "location": event.location,
    }


def _event_from_dict(data: dict) -> Event:
    return Event(
        title=data["title"],
        start=datetime.fromisoformat(data["start"]),
        end=datetime.fromisoformat(data["end"]),
        attendees=tuple(data.get("attendees", ())),
        location=data.get("location"),
    )


def _proposed_meeting_to_dict(meeting: ProposedMeeting) -> dict:
    return {
        "meeting_name": meeting.meeting_name,
        "start": meeting.start.isoformat(),
        "end": meeting.end.isoformat(),
        "participants": list(meeting.participants),
        "source_user_id": meeting.source_user_id,
        "source_adapter_id": meeting.source_adapter_id,
    }


def _proposed_meeting_from_dict(data: dict) -> ProposedMeeting:
    return ProposedMeeting(
        meeting_name=data["meeting_name"],
        start=datetime.fromisoformat(data["start"]),
        end=datetime.fromisoformat(data["end"]),
        participants=tuple(data["participants"]),
        source_user_id=data["source_user_id"],
        source_adapter_id=data["source_adapter_id"],
    )


@dataclass
class Negotiator:
    agent_id: str
    user_id: str
    capabilities: list[str] = field(default_factory=list)
    clock: Callable[[], datetime] = field(default=datetime.now)
    adapters: dict[str, EmailCalendarAdapter] = field(default_factory=dict)

    _sequence_no: int = field(default=0, init=False)
    peers: dict[str, list[str]] = field(default_factory=dict, init=False)
    peer_free_busy: dict[str, list[Event]] = field(default_factory=dict, init=False)
    proposals_emitted: dict[str, list[ProposedMeeting]] = field(default_factory=dict, init=False)
    proposals_received: dict[str, list[ProposedMeeting]] = field(default_factory=dict, init=False)
    proposal_responses: dict[str, dict[str, str]] = field(default_factory=dict, init=False)
    sent_invite_results: dict[str, list[InviteResult]] = field(default_factory=dict, init=False)
    relaxations_received: dict[str, list[dict]] = field(default_factory=dict, init=False)
    _invites_sent_for: set[str] = field(default_factory=set, init=False)

    def hello(self, room_id: str, negotiation_id: str) -> Envelope:
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.HELLO,
            body={"capabilities": list(self.capabilities)},
        )

    def batch_schedule(
        self,
        room_id: str,
        negotiation_id: str,
        meetings: list[MeetingRequest],
        window_start: datetime,
        window_end: datetime,
    ) -> Envelope:
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.BATCH_SCHEDULE,
            body={
                "meetings": [
                    {
                        "name": m.name,
                        "participants": list(m.participants),
                        "duration_minutes": m.duration_minutes,
                    }
                    for m in meetings
                ],
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
            },
        )

    def free_busy(
        self,
        room_id: str,
        negotiation_id: str,
        viewer_user_id: str,
        events: list[Event],
        policy_store: PrivacyPolicyStore,
        window: TimeWindow,
    ) -> Envelope:
        """Emit a FREE_BUSY envelope filtered for one specific viewer.

        ADR 0004: directional per-edge privacy is applied at send time. To honor
        per-viewer policies in a multi-recipient room, the negotiator emits one
        FREE_BUSY message per peer (orchestration concern handled by the caller).
        """
        level = policy_store.get(subject=self.user_id, viewer=viewer_user_id)
        filtered = apply_filter(events, level)
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.FREE_BUSY,
            body={
                "viewer_user_id": viewer_user_id,
                "events": [_event_to_dict(e) for e in filtered],
                "window_start": window.start.isoformat(),
                "window_end": window.end.isoformat(),
                "level": level.value,
            },
        )

    def propose(
        self,
        room_id: str,
        negotiation_id: str,
        proposal_id: str,
        proposed_meetings: list[ProposedMeeting],
    ) -> Envelope:
        self.proposals_emitted[proposal_id] = list(proposed_meetings)
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.PROPOSE,
            body={
                "proposal_id": proposal_id,
                "meetings": [_proposed_meeting_to_dict(m) for m in proposed_meetings],
            },
        )

    def accept(self, room_id: str, negotiation_id: str, proposal_id: str) -> Envelope:
        return self._response(
            room_id, negotiation_id, proposal_id, MessageType.ACCEPT, {}
        )

    def decline(
        self,
        room_id: str,
        negotiation_id: str,
        proposal_id: str,
        reason: str = "",
    ) -> Envelope:
        return self._response(
            room_id, negotiation_id, proposal_id, MessageType.DECLINE, {"reason": reason}
        )

    def counter(
        self,
        room_id: str,
        negotiation_id: str,
        proposal_id: str,
        alternative: list[ProposedMeeting],
    ) -> Envelope:
        return self._response(
            room_id,
            negotiation_id,
            proposal_id,
            MessageType.COUNTER,
            {"alternative": [_proposed_meeting_to_dict(m) for m in alternative]},
        )

    def _response(
        self,
        room_id: str,
        negotiation_id: str,
        proposal_id: str,
        message_type: MessageType,
        extra_body: dict,
    ) -> Envelope:
        body = {"proposal_id": proposal_id}
        body.update(extra_body)
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=message_type,
            body=body,
        )

    def has_unanimous_accept(
        self, proposal_id: str, expected_responders: set[str]
    ) -> bool:
        responses = self.proposal_responses.get(proposal_id, {})
        return (
            set(responses.keys()) >= expected_responders
            and all(
                responses[agent_id] == MessageType.ACCEPT.value
                for agent_id in expected_responders
            )
        )

    def deadlock_relax(
        self,
        room_id: str,
        negotiation_id: str,
        proposal_id: str,
        relaxation_kind: str,
        details: dict,
    ) -> Envelope:
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.DEADLOCK_RELAX,
            body={
                "proposal_id": proposal_id,
                "relaxation_kind": relaxation_kind,
                "details": details,
            },
        )

    def deadlock_ask(
        self,
        room_id: str,
        negotiation_id: str,
        proposal_id: str,
        binding_users: list[str],
        suggestion: str = "",
    ) -> Envelope:
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.DEADLOCK_ASK,
            body={
                "proposal_id": proposal_id,
                "binding_users": list(binding_users),
                "suggestion": suggestion,
            },
        )

    def confirm(
        self, room_id: str, negotiation_id: str, proposal_id: str
    ) -> Envelope:
        """Emit CONFIRM and send invites for any meetings this negotiator owns."""
        self._send_invites_for_owned_meetings(proposal_id)
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.CONFIRM,
            body={"proposal_id": proposal_id},
        )

    def _send_invites_for_owned_meetings(self, proposal_id: str) -> None:
        if proposal_id in self._invites_sent_for:
            return  # idempotent across confirm() and receive(CONFIRM)
        meetings = self.proposals_emitted.get(proposal_id) or self.proposals_received.get(proposal_id) or []
        for meeting in meetings:
            if meeting.source_user_id != self.user_id:
                continue
            adapter = self.adapters.get(meeting.source_adapter_id)
            if adapter is None:
                continue
            invite = MeetingInvite(
                title=meeting.meeting_name,
                start=meeting.start,
                end=meeting.end,
                attendees=meeting.participants,
            )
            result = adapter.send_invite(invite)
            self.sent_invite_results.setdefault(proposal_id, []).append(result)
        self._invites_sent_for.add(proposal_id)

    def receive(self, envelope: Envelope) -> None:
        if envelope.message_type == MessageType.HELLO:
            self.peers[envelope.sender_agent_id] = list(
                envelope.body.get("capabilities", [])
            )
        elif envelope.message_type == MessageType.FREE_BUSY:
            if envelope.body.get("viewer_user_id") == self.user_id:
                self.peer_free_busy[envelope.sender_agent_id] = [
                    _event_from_dict(d) for d in envelope.body.get("events", [])
                ]
        elif envelope.message_type == MessageType.PROPOSE:
            proposal_id = envelope.body["proposal_id"]
            self.proposals_received[proposal_id] = [
                _proposed_meeting_from_dict(d) for d in envelope.body["meetings"]
            ]
        elif envelope.message_type in (
            MessageType.ACCEPT,
            MessageType.DECLINE,
            MessageType.COUNTER,
        ):
            proposal_id = envelope.body["proposal_id"]
            self.proposal_responses.setdefault(proposal_id, {})[
                envelope.sender_agent_id
            ] = envelope.message_type.value
        elif envelope.message_type == MessageType.CONFIRM:
            proposal_id = envelope.body.get("proposal_id")
            if proposal_id:
                self._send_invites_for_owned_meetings(proposal_id)
        elif envelope.message_type == MessageType.DEADLOCK_RELAX:
            proposal_id = envelope.body.get("proposal_id")
            if proposal_id:
                self.relaxations_received.setdefault(proposal_id, []).append(
                    {
                        "kind": envelope.body.get("relaxation_kind"),
                        "details": envelope.body.get("details", {}),
                        "user_id": envelope.sender_user_id,
                    }
                )

    # --- Slice 19: state persistence (crash recovery) ---

    def save_state(self, path: Path) -> None:
        state = {
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "capabilities": list(self.capabilities),
            "_sequence_no": self._sequence_no,
            "peers": self.peers,
            "peer_free_busy": {
                agent_id: [_event_to_dict(e) for e in events]
                for agent_id, events in self.peer_free_busy.items()
            },
            "proposals_emitted": {
                pid: [_proposed_meeting_to_dict(m) for m in meetings]
                for pid, meetings in self.proposals_emitted.items()
            },
            "proposals_received": {
                pid: [_proposed_meeting_to_dict(m) for m in meetings]
                for pid, meetings in self.proposals_received.items()
            },
            "proposal_responses": self.proposal_responses,
            "relaxations_received": self.relaxations_received,
            "_invites_sent_for": list(self._invites_sent_for),
        }
        path.write_text(json.dumps(state))

    def load_state(self, path: Path) -> None:
        state = json.loads(path.read_text())
        if state["agent_id"] != self.agent_id:
            raise ValueError(
                f"State file is for agent {state['agent_id']!r}, "
                f"refusing to load into {self.agent_id!r}"
            )
        self._sequence_no = state["_sequence_no"]
        self.peers = dict(state.get("peers", {}))
        self.peer_free_busy = {
            agent_id: [_event_from_dict(d) for d in events]
            for agent_id, events in state.get("peer_free_busy", {}).items()
        }
        self.proposals_emitted = {
            pid: [_proposed_meeting_from_dict(d) for d in meetings]
            for pid, meetings in state.get("proposals_emitted", {}).items()
        }
        self.proposals_received = {
            pid: [_proposed_meeting_from_dict(d) for d in meetings]
            for pid, meetings in state.get("proposals_received", {}).items()
        }
        self.proposal_responses = dict(state.get("proposal_responses", {}))
        self.relaxations_received = dict(state.get("relaxations_received", {}))
        self._invites_sent_for = set(state.get("_invites_sent_for", []))

    def _next_seq(self) -> int:
        seq = self._sequence_no
        self._sequence_no += 1
        return seq
