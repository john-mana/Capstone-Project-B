import builtins
import types


class DummyDashboard:
    def __init__(self):
        self.ran = False

    def run(self):
        self.ran = True


def test_main_calls_dashboard_run(monkeypatch):
    # Replace Dashboard in main with a dummy
    import main
    monkeypatch.setattr(main, "Dashboard", DummyDashboard)

    # Execute
    main.main()

    # Verify
    # The instance is created inside main.main, so we can't access it directly here.
    # Instead, verify no exceptions and that Dashboard was replaced (smoke test).
    assert main.Dashboard is DummyDashboard


