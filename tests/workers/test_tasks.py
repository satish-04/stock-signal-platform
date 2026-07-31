from app.workers import tasks


def test_all_background_actors_are_registered() -> None:
    actors = {
        tasks.workflow_reconciliation.actor_name,
        tasks.execution_reconciliation.actor_name,
        tasks.position_reconciliation.actor_name,
        tasks.exit_monitoring.actor_name,
        tasks.stale_workflow_cleanup.actor_name,
    }
    assert actors == {
        "workflow_reconciliation",
        "execution_reconciliation",
        "position_reconciliation",
        "exit_monitoring",
        "stale_workflow_cleanup",
    }


def test_schedule_bucket_is_stable(monkeypatch) -> None:
    class FakeDateTime:
        @staticmethod
        def now(_timezone):
            class Result:
                @staticmethod
                def timestamp():
                    return 125.0

            return Result()

    monkeypatch.setattr(tasks, "datetime", FakeDateTime)
    assert tasks._schedule_bucket(60) == "120"
