import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


class DailyLossScopeTests(unittest.TestCase):
    def test_scoped_daily_pnl_counts_only_matching_symbol_and_magic(self) -> None:
        from daily_loss_scope import calculate_scoped_daily_pnl

        deals = [
            SimpleNamespace(symbol="GBPUSDm", magic=20250314, profit=-1.20, commission=-0.10, swap=0.00, fee=0.00),
            SimpleNamespace(symbol="GBPUSDm", magic=20250314, profit=0.00, commission=-0.05, swap=0.00, fee=0.00),
            SimpleNamespace(symbol="USTECm", magic=2026031301, profit=-3.50, commission=0.00, swap=0.00, fee=0.00),
            SimpleNamespace(symbol="GBPUSDm", magic=999999, profit=-9.99, commission=0.00, swap=0.00, fee=0.00),
        ]
        positions = [
            SimpleNamespace(symbol="GBPUSDm", magic=20250314, profit=-0.65, swap=-0.02),
            SimpleNamespace(symbol="USTECm", magic=2026031301, profit=1.40, swap=0.00),
            SimpleNamespace(symbol="GBPUSDm", magic=999999, profit=-4.00, swap=0.00),
        ]

        pnl = calculate_scoped_daily_pnl(
            deals,
            positions,
            symbol="GBPUSDm",
            magic=20250314,
        )

        self.assertAlmostEqual(pnl, -2.02)

    def test_fetch_scoped_daily_pnl_uses_current_utc_day_window(self) -> None:
        from daily_loss_scope import fetch_scoped_daily_pnl

        class FakeMt5:
            def __init__(self) -> None:
                self.deals_args = None

            def history_deals_get(self, start, end):
                self.deals_args = (start, end)
                return [
                    SimpleNamespace(symbol="USTECm", magic=2026031301, profit=-2.00, commission=0.00, swap=0.00, fee=0.00)
                ]

            def positions_get(self):
                return [
                    SimpleNamespace(symbol="USTECm", magic=2026031301, profit=-0.50, swap=-0.10),
                ]

        now = datetime(2026, 3, 19, 14, 45, tzinfo=timezone.utc)
        mt5 = FakeMt5()

        pnl = fetch_scoped_daily_pnl(mt5, symbol="USTECm", magic=2026031301, now=now)

        self.assertAlmostEqual(pnl, -2.60)
        self.assertEqual(
            mt5.deals_args,
            (
                datetime(2026, 3, 19, 0, 0, tzinfo=timezone.utc),
                datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc),
            ),
        )

    def test_runtimes_use_scoped_daily_pnl_helper(self) -> None:
        forex_source = (ROOT / "forex_grid_engine.py").read_text(encoding="utf-8")
        nas100_source = (ROOT / "nas100_grid_bot.py").read_text(encoding="utf-8")

        self.assertIn("fetch_scoped_daily_pnl", forex_source)
        self.assertIn("fetch_scoped_daily_pnl", nas100_source)
        self.assertNotIn("daily_start_equity = None", forex_source)
        self.assertNotIn("daily_start_equity = None", nas100_source)


if __name__ == "__main__":
    unittest.main()
