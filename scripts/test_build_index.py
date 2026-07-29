"""Tests for build_index. Standard library only: python3 -m unittest."""
import tempfile
import unittest
from datetime import date
from pathlib import Path

import build_index


HEAD = """<!DOCTYPE html>
<html><head>
<title>{title}</title>
{meta}
</head><body>ok</body></html>
"""


def write_game(root, slug, title="Test Game", meta=None):
    """Create root/games/<slug>/index.html and return its path."""
    if meta is None:
        meta = (
            '<meta name="description" content="A test game.">\n'
            '<meta name="added" content="2026-01-15">'
        )
    game_dir = root / "games" / slug
    game_dir.mkdir(parents=True, exist_ok=True)
    path = game_dir / "index.html"
    path.write_text(HEAD.format(title=title, meta=meta), encoding="utf-8")
    return path


class BuilderTestCase(unittest.TestCase):
    """Points build_index at a throwaway tree instead of the real repo."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._real_root = build_index.ROOT
        self._real_games = build_index.GAMES_DIR
        build_index.ROOT = self.root
        build_index.GAMES_DIR = self.root / "games"
        (self.root / "games").mkdir()

    def tearDown(self):
        build_index.ROOT = self._real_root
        build_index.GAMES_DIR = self._real_games
        self._tmp.cleanup()


class TestFindGames(BuilderTestCase):
    def test_finds_one_level_of_game_folders(self):
        write_game(self.root, "alpha")
        write_game(self.root, "beta")
        found = build_index.find_games(self.root / "games")
        self.assertEqual([p.parent.name for p in found], ["alpha", "beta"])

    def test_ignores_deeper_nesting(self):
        deep = self.root / "games" / "alpha" / "nested"
        deep.mkdir(parents=True)
        (deep / "index.html").write_text("<title>x</title>", encoding="utf-8")
        found = build_index.find_games(self.root / "games")
        self.assertEqual(found, [])

    def test_missing_games_dir_is_not_an_error(self):
        self.assertEqual(build_index.find_games(self.root / "nope"), [])


class TestParseGame(BuilderTestCase):
    def test_parses_a_complete_game(self):
        path = write_game(
            self.root,
            "safeguarded-copy",
            title="SGC Game",
            meta=(
                '<meta name="description" content="Roll it back.">\n'
                '<meta name="added" content="2026-07-29">\n'
                '<meta name="keywords" content="arcade, storage ,  IBM">\n'
                '<meta name="game-accent" content="#36e0c8">\n'
                '<meta name="game-controls" content="Arrows or WASD">'
            ),
        )
        game, errors = build_index.parse_game(path)
        self.assertEqual(errors, [])
        self.assertEqual(game.slug, "safeguarded-copy")
        self.assertEqual(game.title, "SGC Game")
        self.assertEqual(game.description, "Roll it back.")
        self.assertEqual(game.added, date(2026, 7, 29))
        self.assertEqual(game.tags, ["arcade", "storage", "IBM"])
        self.assertEqual(game.accent, "#36e0c8")
        self.assertEqual(game.controls, "Arrows or WASD")
        self.assertIsNone(game.cover)

    def test_optional_fields_fall_back(self):
        path = write_game(self.root, "plain")
        game, errors = build_index.parse_game(path)
        self.assertEqual(errors, [])
        self.assertEqual(game.tags, [])
        self.assertEqual(game.accent, build_index.DEFAULT_ACCENT)
        self.assertEqual(game.controls, "")

    def test_missing_description_is_an_error(self):
        path = write_game(
            self.root, "bad", meta='<meta name="added" content="2026-01-15">'
        )
        game, errors = build_index.parse_game(path)
        self.assertIsNone(game)
        self.assertEqual(len(errors), 1)
        self.assertIn("description", errors[0])
        self.assertIn("games/bad/index.html", errors[0])

    def test_collects_every_error_not_just_the_first(self):
        path = write_game(self.root, "bad", title="", meta="")
        game, errors = build_index.parse_game(path)
        self.assertIsNone(game)
        self.assertEqual(len(errors), 3)

    def test_unparseable_added_date_is_an_error(self):
        path = write_game(
            self.root,
            "bad",
            meta=(
                '<meta name="description" content="d">\n'
                '<meta name="added" content="last Tuesday">'
            ),
        )
        game, errors = build_index.parse_game(path)
        self.assertIsNone(game)
        self.assertIn("YYYY-MM-DD", errors[0])

    def test_non_hex_accent_is_an_error(self):
        path = write_game(
            self.root,
            "bad",
            meta=(
                '<meta name="description" content="d">\n'
                '<meta name="added" content="2026-01-15">\n'
                '<meta name="game-accent" content="cyan">'
            ),
        )
        game, errors = build_index.parse_game(path)
        self.assertIsNone(game)
        self.assertIn("hex colour", errors[0])

    def test_entities_in_meta_are_decoded(self):
        path = write_game(
            self.root,
            "amp",
            title="Snapshot &amp; Recover",
            meta=(
                '<meta name="description" content="Back &amp; forth.">\n'
                '<meta name="added" content="2026-01-15">'
            ),
        )
        game, errors = build_index.parse_game(path)
        self.assertEqual(errors, [])
        self.assertEqual(game.title, "Snapshot & Recover")
        self.assertEqual(game.description, "Back & forth.")


if __name__ == "__main__":
    unittest.main()
