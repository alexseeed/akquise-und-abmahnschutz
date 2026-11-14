"""Skill-Einträge für Claude Code und Codex sind vorhanden und aktuell.

Die Einträge unter .claude/skills/<skill>/SKILL.md und .agents/skills/<skill>/SKILL.md
tragen den Frontmatter des echten <skill>/SKILL.md wörtlich. Ändert jemand die
Beschreibung im echten Skill, muss er die Einträge mitziehen – sonst wird dieser
Test rot.

    python3 -m unittest test_skill_eintraege -v   (aus lead-scraper/werkzeuge/)
"""
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parent
PAKET = HIER.parent.parent  # Paketordner mit lead-scraper/ und abmahnung-werbemail-abwehr/
SKILLS = ["lead-scraper", "abmahnung-werbemail-abwehr"]
ORTE = [".claude/skills", ".agents/skills"]


def frontmatter(text):
    """Kopf zwischen den ersten beiden --- Zeilen; None ohne gültigen Kopf."""
    teile = text.split("---", 2)
    if not text.startswith("---") or len(teile) < 3 or "name:" not in teile[1]:
        return None
    return teile[1]


class SkillEintraegeTest(unittest.TestCase):
    def test_eintraege_vorhanden_kein_symlink_frontmatter_identisch(self):
        for skill in SKILLS:
            echt = PAKET / skill / "SKILL.md"
            kopf_echt = frontmatter(echt.read_text(encoding="utf-8"))
            self.assertIsNotNone(kopf_echt, f"{skill}/SKILL.md hat keinen Kopf mit name und description")
            for ort in ORTE:
                with self.subTest(skill=skill, ort=ort):
                    eintrag = PAKET / ort / skill / "SKILL.md"
                    self.assertTrue(eintrag.is_file(), f"{eintrag.relative_to(PAKET)} fehlt")
                    self.assertFalse(eintrag.is_symlink(), f"{eintrag.relative_to(PAKET)} ist ein Symlink (Windows)")
                    kopf = frontmatter(eintrag.read_text(encoding="utf-8"))
                    self.assertIsNotNone(kopf, f"{eintrag.relative_to(PAKET)} hat keinen Kopf")
                    self.assertEqual(kopf, kopf_echt,
                                     f"Frontmatter in {eintrag.relative_to(PAKET)} weicht von {skill}/SKILL.md ab")


if __name__ == "__main__":
    unittest.main()
