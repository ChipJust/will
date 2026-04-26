"""MeetingPattern — the recurring scheduling rhythm declared per group.

For the cohort, this is `1 cohort meeting + N triad meetings per month`. The
pattern is what `BATCH_SCHEDULE` ultimately negotiates over.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class RecurringMeetingSpec:
    name: str
    participants: tuple[str, ...]
    duration_minutes: int
    count_per_period: int = 1
    period: str = "month"


@dataclass
class MeetingPattern:
    group_id: str
    recurring_meetings: list[RecurringMeetingSpec] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "group_id": self.group_id,
                "recurring_meetings": [
                    {
                        "name": spec.name,
                        "participants": list(spec.participants),
                        "duration_minutes": spec.duration_minutes,
                        "count_per_period": spec.count_per_period,
                        "period": spec.period,
                    }
                    for spec in self.recurring_meetings
                ],
            }
        )

    @classmethod
    def from_json(cls, data: str) -> MeetingPattern:
        parsed = json.loads(data)
        return cls(
            group_id=parsed["group_id"],
            recurring_meetings=[
                RecurringMeetingSpec(
                    name=item["name"],
                    participants=tuple(item["participants"]),
                    duration_minutes=item["duration_minutes"],
                    count_per_period=item.get("count_per_period", 1),
                    period=item.get("period", "month"),
                )
                for item in parsed.get("recurring_meetings", [])
            ],
        )
