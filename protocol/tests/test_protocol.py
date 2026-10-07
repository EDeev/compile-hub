import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from compilehub_protocol import CLIENT_MESSAGE, EVENT, Exit, Job, Limits, Result, StdinData, Stdout, Verdict


def test_job_roundtrip():
    job = Job(run_id=uuid4(), language="cpp", code="int main(){}", limits=Limits(wall_ms=1000))
    assert Job.model_validate_json(job.dump()) == job


def test_events_are_camel_case_for_the_client():
    raw = json.loads(Exit(verdict=Verdict.OK, exit_code=0, time_ms=12, memory_kb=3412).dump())
    assert raw == {"type": "exit", "verdict": "OK", "exitCode": 0, "timeMs": 12, "memoryKb": 3412}


def test_event_union_dispatches_by_type():
    assert EVENT.validate_json('{"type": "stdout", "data": "hi"}') == Stdout(data="hi")
    with pytest.raises(ValidationError):
        EVENT.validate_json('{"type": "nope"}')


def test_client_messages():
    assert CLIENT_MESSAGE.validate_json('{"type": "stdin", "data": "42\\n"}') == StdinData(data="42\n")
    with pytest.raises(ValidationError):
        CLIENT_MESSAGE.validate_json('{"type": "exit", "verdict": "OK"}')


def test_result_omits_empty_fields():
    run_id = uuid4()
    assert json.loads(Result(run_id=run_id, verdict=Verdict.CANCELLED).dump()) == {
        "runId": str(run_id),
        "verdict": "CANCELLED",
        "output": "",
    }
