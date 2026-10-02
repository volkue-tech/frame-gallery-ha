"""The in-process executor seam (§11.3, D-139) and lazy worker imports (D-107)."""

from __future__ import annotations

import ast
import subprocess
import sys
import types
from pathlib import Path
from typing import cast

import pytest

from frame_gallery.errors import Cancelled
from frame_gallery.imaging import contract
from frame_gallery.isolation import in_process
from frame_gallery.isolation.executor import (
    EventSink,
    Executor,
    JsonObject,
    TaskFunction,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.isolation.in_process import (
    INSPECT_TASK,
    PREPARE_TASK,
    InProcessExecutor,
    default_event_tasks,
    default_executor,
    default_tasks,
)
from tests.support.clock import FakeClock

SRC = Path(__file__).resolve().parents[3] / "src"
WORKER_TASKS = "frame_gallery.imaging.worker_tasks"


class Tasks:
    """Task functions that record their requests."""

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.requests: list[JsonObject] = []

    def echo(self, payload: JsonObject) -> JsonObject:
        self.requests.append(payload)
        return {"echo": payload}

    def slow(self, payload: JsonObject) -> JsonObject:
        seconds = payload["seconds"]
        assert isinstance(seconds, float)
        self.clock.advance(seconds)
        return {"done": True}

    def crash(self, payload: JsonObject) -> JsonObject:
        msg = "hostile detail from inside the task"
        raise RuntimeError(msg)

    def memory(self, payload: JsonObject) -> JsonObject:
        raise MemoryError

    def cancel(self, payload: JsonObject) -> JsonObject:
        msg = "stop requested"
        raise Cancelled(msg)

    def interrupt(self, payload: JsonObject) -> JsonObject:
        raise KeyboardInterrupt

    def not_an_object(self, payload: JsonObject) -> JsonObject:
        return cast("JsonObject", ["a", "list"])

    def not_finite(self, payload: JsonObject) -> JsonObject:
        return {"value": float("nan")}

    def huge(self, payload: JsonObject) -> JsonObject:
        return {"blob": "x" * 70_000}

    def table(self) -> dict[str, TaskFunction]:
        return {
            "echo": self.echo,
            "slow": self.slow,
            "crash": self.crash,
            "memory": self.memory,
            "cancel": self.cancel,
            "interrupt": self.interrupt,
            "not_an_object": self.not_an_object,
            "not_finite": self.not_finite,
            "huge": self.huge,
        }


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def tasks(clock: FakeClock) -> Tasks:
    return Tasks(clock)


@pytest.fixture
def executor(tasks: Tasks, clock: FakeClock) -> InProcessExecutor:
    return InProcessExecutor(tasks.table(), clock)


def test_implements_the_executor_protocol(executor: InProcessExecutor) -> None:
    seam: Executor = executor
    assert seam.run("echo", {}, timeout=1.0) == {"echo": {}}


def test_run_returns_the_decoded_result(executor: InProcessExecutor, tasks: Tasks) -> None:
    payload: JsonObject = {"path": "in/source.jpg", "limits": [1, 2]}
    assert executor.run("echo", payload, timeout=15.0) == {"echo": payload}
    assert tasks.requests == [payload]


def test_the_task_receives_a_decoded_copy(executor: InProcessExecutor, tasks: Tasks) -> None:
    payload: JsonObject = {"nested": {"k": [1]}}
    executor.run("echo", payload, timeout=1.0)
    assert tasks.requests[0] == payload
    assert tasks.requests[0] is not payload
    assert tasks.requests[0]["nested"] is not payload["nested"]


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("nan")])
def test_run_requires_a_positive_timeout(executor: InProcessExecutor, timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        executor.run("echo", {}, timeout=timeout)


def test_unknown_task(executor: InProcessExecutor) -> None:
    with pytest.raises(WorkerError) as caught:
        executor.run("inspect\nforged", {}, timeout=1.0)
    assert caught.value.kind is WorkerErrorKind.UNKNOWN_TASK
    assert caught.value.detail == "inspect forged"


def test_invalid_request_is_a_protocol_error(executor: InProcessExecutor, tasks: Tasks) -> None:
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {"value": float("inf")}, timeout=1.0)
    assert caught.value.kind is WorkerErrorKind.PROTOCOL
    assert caught.value.detail.startswith("request: ")
    assert tasks.requests == []


def test_oversize_request_is_a_protocol_error(tasks: Tasks, clock: FakeClock) -> None:
    executor = InProcessExecutor(tasks.table(), clock, max_message_bytes=16)
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {"s": "x" * 32}, timeout=1.0)
    assert caught.value.kind is WorkerErrorKind.PROTOCOL
    assert tasks.requests == []


def test_task_exception_is_a_crash_with_the_type_name_only(executor: InProcessExecutor) -> None:
    with pytest.raises(WorkerError) as caught:
        executor.run("crash", {}, timeout=1.0)
    error = caught.value
    assert error.kind is WorkerErrorKind.CRASH
    assert error.detail == "RuntimeError"
    assert "hostile" not in str(error)
    assert error.__cause__ is None
    assert error.__suppress_context__


def test_memory_error_is_a_memory_failure(executor: InProcessExecutor) -> None:
    with pytest.raises(WorkerError) as caught:
        executor.run("memory", {}, timeout=1.0)
    assert caught.value.kind is WorkerErrorKind.MEMORY


def test_cancelled_propagates_unchanged(executor: InProcessExecutor) -> None:
    with pytest.raises(Cancelled, match="stop requested"):
        executor.run("cancel", {}, timeout=1.0)


def test_base_exceptions_are_not_swallowed(executor: InProcessExecutor) -> None:
    with pytest.raises(KeyboardInterrupt):
        executor.run("interrupt", {}, timeout=1.0)


def test_task_that_outlives_its_timeout_is_discarded(
    executor: InProcessExecutor, clock: FakeClock
) -> None:
    with pytest.raises(WorkerError) as caught:
        executor.run("slow", {"seconds": 15.5}, timeout=15.0)
    assert caught.value.kind is WorkerErrorKind.TIMEOUT
    assert caught.value.detail == "15.5 s > 15.0 s"
    assert clock.elapsed == 15.5


def test_task_that_uses_exactly_its_timeout_succeeds(executor: InProcessExecutor) -> None:
    assert executor.run("slow", {"seconds": 15.0}, timeout=15.0) == {"done": True}


def test_timeout_is_checked_before_the_result(tasks: Tasks, clock: FakeClock) -> None:
    def slow_and_invalid(payload: JsonObject) -> JsonObject:
        clock.advance(2.0)
        return {"value": float("nan")}

    executor = InProcessExecutor({"task": slow_and_invalid}, clock)
    with pytest.raises(WorkerError) as caught:
        executor.run("task", {}, timeout=1.0)
    assert caught.value.kind is WorkerErrorKind.TIMEOUT


@pytest.mark.parametrize("task", ["not_an_object", "not_finite", "huge"])
def test_invalid_result_is_a_protocol_error(executor: InProcessExecutor, task: str) -> None:
    with pytest.raises(WorkerError) as caught:
        executor.run(task, {}, timeout=1.0)
    assert caught.value.kind is WorkerErrorKind.PROTOCOL
    assert caught.value.detail.startswith("result: ")


def test_terminate_all_is_a_repeatable_no_op(executor: InProcessExecutor) -> None:
    executor.terminate_all()
    executor.terminate_all()
    assert executor.run("echo", {}, timeout=1.0) == {"echo": {}}


def test_the_task_table_is_copied(tasks: Tasks, clock: FakeClock) -> None:
    table = tasks.table()
    executor = InProcessExecutor(table, clock)
    table.clear()
    assert executor.run("echo", {}, timeout=1.0) == {"echo": {}}


# --- default tasks and lazy imports (D-107) ---------------------------------


def test_default_tasks_offer_prepare_and_inspect() -> None:
    """Prepare returns one result; inspect reports each file as an event."""
    assert set(default_tasks()) == {PREPARE_TASK} == {"prepare"}
    assert set(default_event_tasks()) == {INSPECT_TASK} == {"inspect"}
    assert (contract.PREPARE_TASK, contract.INSPECT_TASK) == (PREPARE_TASK, INSPECT_TASK)


def test_inspect_imports_the_worker_module_when_it_runs(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    received: list[JsonObject] = []

    def inspect_task(payload: JsonObject, emit: EventSink) -> JsonObject:
        received.append(payload)
        emit({"index": 0})
        return {"inspected": 1}

    fake = types.ModuleType(WORKER_TASKS)
    fake.inspect_task = inspect_task  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, WORKER_TASKS, fake)
    events: list[JsonObject] = []
    result = default_executor(clock).run(
        "inspect", {"files": []}, timeout=2.0, on_event=events.append
    )
    assert result == {"inspected": 1}
    assert received == [{"files": []}]
    assert events == [{"index": 0}]


def test_prepare_imports_the_worker_module_when_it_runs(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    received: list[JsonObject] = []

    def prepare_task(payload: JsonObject) -> JsonObject:
        received.append(payload)
        return {"status": "prepared"}

    fake = types.ModuleType(WORKER_TASKS)
    fake.prepare_task = prepare_task  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, WORKER_TASKS, fake)

    executor = InProcessExecutor(default_tasks(), clock)
    assert executor.run("prepare", {"source": "in/a.jpg"}, timeout=15.0) == {"status": "prepared"}
    assert received == [{"source": "in/a.jpg"}]


def test_the_module_never_imports_worker_tasks_statically() -> None:
    tree = ast.parse(Path(in_process.__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
            imported.extend(f"{node.module}.{alias.name}" for alias in node.names)
    assert imported
    assert not [name for name in imported if "worker_tasks" in name or "PIL" in name]


def test_importing_the_executor_does_not_load_pillow() -> None:
    code = (
        "import sys\n"
        "import frame_gallery.isolation.in_process as module\n"
        "from frame_gallery.budget.clock import SystemClock\n"
        "module.default_executor(SystemClock())\n"
        "loaded = [n for n in sys.modules if n.split('.')[0] == 'PIL' or 'worker_tasks' in n]\n"
        "print(loaded)\n"
    )
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and code
        [sys.executable, "-c", code],
        env={"PYTHONPATH": str(SRC)},
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    assert completed.stdout.strip() == "[]"


class TestEvents:
    """Event tasks, event delivery, and stop requests (D-141, Phase 5)."""

    def executor(self, clock: FakeClock) -> InProcessExecutor:
        def markers(payload: JsonObject, emit: EventSink) -> JsonObject:
            for name in ("a", "b", "c"):
                emit({"marker": name})
            return {"done": True}

        def bad_event(payload: JsonObject, emit: EventSink) -> JsonObject:
            emit({"value": float("nan")})
            return {}

        return InProcessExecutor(
            {"plain": lambda payload: {"plain": True}},
            clock,
            event_tasks={"markers": markers, "bad_event": bad_event},
        )

    def test_events_arrive_in_order_before_the_result(self, clock: FakeClock) -> None:
        seen: list[JsonObject] = []
        result = self.executor(clock).run("markers", {}, timeout=1.0, on_event=seen.append)
        assert seen == [{"marker": "a"}, {"marker": "b"}, {"marker": "c"}]
        assert result == {"done": True}

    def test_events_without_a_sink_are_dropped(self, clock: FakeClock) -> None:
        assert self.executor(clock).run("markers", {}, timeout=1.0) == {"done": True}

    def test_plain_tasks_still_run(self, clock: FakeClock) -> None:
        assert self.executor(clock).run("plain", {}, timeout=1.0) == {"plain": True}

    def test_a_stop_ends_the_task_after_the_current_event(self, clock: FakeClock) -> None:
        seen: list[JsonObject] = []
        with pytest.raises(WorkerError) as caught:
            self.executor(clock).run(
                "markers",
                {},
                timeout=1.0,
                on_event=seen.append,
                should_stop=lambda: len(seen) >= 2,
            )
        assert caught.value.kind is WorkerErrorKind.STOPPED
        assert seen == [{"marker": "a"}, {"marker": "b"}]

    def test_a_stop_before_the_start_runs_nothing(self, clock: FakeClock) -> None:
        seen: list[JsonObject] = []
        with pytest.raises(WorkerError) as caught:
            self.executor(clock).run(
                "markers", {}, timeout=1.0, on_event=seen.append, should_stop=lambda: True
            )
        assert caught.value.kind is WorkerErrorKind.STOPPED
        assert seen == []

    def test_a_refused_event_is_a_protocol_error(self, clock: FakeClock) -> None:
        def refuse(event: JsonObject) -> None:
            msg = "out of order"
            raise ValueError(msg)

        with pytest.raises(WorkerError) as caught:
            self.executor(clock).run("markers", {}, timeout=1.0, on_event=refuse)
        assert caught.value.kind is WorkerErrorKind.PROTOCOL
        assert "out of order" in str(caught.value)

    def test_an_invalid_event_is_a_protocol_error(self, clock: FakeClock) -> None:
        with pytest.raises(WorkerError) as caught:
            self.executor(clock).run("bad_event", {}, timeout=1.0, on_event=lambda e: None)
        assert caught.value.kind is WorkerErrorKind.PROTOCOL
