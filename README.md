# Arcade

Playable browser games, hosted on GitHub Pages: https://triippiing.github.io/Arcade/

Everything runs client side. There is no server, no database, and no analytics.
High scores are saved in each player's own browser via localStorage and are never
uploaded, so scores are per person and per browser.

## Adding a game

1. Create `games/<slug>/index.html`. The slug is lowercase kebab-case and becomes
   the URL: `games/space-mines/` serves at `/Arcade/games/space-mines/`.
2. Declare the game in its `<head>`:

   | Tag | Required | Notes |
   |---|---|---|
   | `<title>` | yes | Card title |
   | `<meta name="description">` | yes | One line blurb |
   | `<meta name="added" content="YYYY-MM-DD">` | yes | Sort key, and a New badge for 30 days |
   | `<meta name="keywords">` | no | Comma separated, rendered as chips |
   | `<meta name="game-accent" content="#36e0c8">` | no | Card accent colour |
   | `<meta name="game-controls">` | no | For example `Arrows or WASD` |

3. Optionally drop a `cover.png`, `cover.jpg`, or `cover.webp` in the same folder.
   Without one the index generates a monogram tile from the slug.
4. Push to `main`. The Build index workflow regenerates `index.html` and commits
   it back, which redeploys the site.

A missing required tag fails the build rather than producing a half empty card.
Run `python3 scripts/build_index.py` locally to see the errors before pushing.

## Local preview

```bash
./serve.sh     # http://localhost:8000/
```

## Tests

```bash
python3 -m unittest discover -s scripts -t scripts -v
```

Standard library only. No dependencies to install.

## Hosting your own copy

Fork or clone this repo into your own account, then enable Pages in Settings with
the source set to the `main` branch, root folder. Your copy will serve at
`https://<your-user>.github.io/<your-repo-name>/`.

Every path in this site is relative, so it works under any repo name, under a
custom domain, and straight off the filesystem. Nothing is tied to this account.

Two notes for a fork:

- GitHub disables Actions on forks by default. Enable them under the Actions tab
  if you want the index to rebuild automatically. Nothing breaks if you do not:
  `index.html` is a committed file, it just will not refresh on its own.
- Scores are stored per origin, so your visitors' leaderboards are separate from
  this site's.
