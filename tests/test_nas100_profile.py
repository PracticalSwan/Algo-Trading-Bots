import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    ROOT / "nas100_grid_bot.py.template",
    ROOT / "nas100_grid_bot.py",
]

EXPECTED_CONSTANTS = {
    "LOT_MULTIPLIER": 1.00,
    "MAX_LOT": 0.02,
    "MAX_LEVELS": 4,
    "GROWTH_LOT_EXPONENT": 0.50,
    "GRID_ATR_MULTIPLIER": 1.00,
    "MIN_GRID_STEP_PRICE": 18.0,
}


def load_assignments(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            try:
                assignments[name] = ast.literal_eval(node.value)
            except Exception:
                continue
    return assignments


class Nas100ConservativeProfileTests(unittest.TestCase):
    def test_profile_constants_match_conservative_targets(self) -> None:
        for path in TARGET_FILES:
            with self.subTest(path=path.name):
                assignments = load_assignments(path)
                for name, expected in EXPECTED_CONSTANTS.items():
                    self.assertEqual(assignments.get(name), expected)

    def test_startup_banner_uses_conservative_label(self) -> None:
        for path in TARGET_FILES:
            with self.subTest(path=path.name):
                contents = path.read_text(encoding="utf-8")
                self.assertIn("CONSERVATIVE", contents)
                self.assertNotIn("Aggressive Grid Bot", contents)
                self.assertNotIn("AGGRESSIVE GRID BOT", contents)


if __name__ == "__main__":
    unittest.main()
