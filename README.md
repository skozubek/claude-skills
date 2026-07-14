# claude-skills

Private monorepo for custom Claude Code skills + commands that live globally in
`~/.claude/` via symlink. One `git pull` + `bootstrap.sh` brings a fresh Mac up to date.

## Layout

```
claude-skills/
├── bootstrap.sh          # idempotent: re-creates all symlinks + fetches teach
├── wiki-compile/         # Karpathy-style LLM wiki compiler (global skill)
├── wiki-query/           # wiki Q&A (global skill)
├── wiki-brief/           # morning push briefing of the project wiki
├── wiki-health/          # wiki semantic + operational health audit
├── mol-report/           # cross-project MOL weekly note + monthly invoice (git-scans ~/Coding/MOL/*)
├── devils-advocate/      # anti-sycophancy diagnostic — force the opposite argument
├── reflect/              # abstract a recurring mistake into a persisted learning
├── transcribe/           # Obsidian audio → structured meeting note (mlx_whisper, Apple Silicon)
└── commands/
    └── debrief.md        # /debrief — drill on work just done (sister to /teach)
```

## What syncs how

| Thing                | Mechanism            | Notes                                              |
|----------------------|----------------------|----------------------------------------------------|
| wiki-* skills        | git + symlink        | this repo → `~/.claude/skills/`                     |
| mol-report skill     | git + symlink        | this repo → `~/.claude/skills/`; needs `~/Coding/MOL/` repos cloned to run |
| `/debrief` command   | git + symlink        | this repo → `~/.claude/commands/`                   |
| `/teach` skill (Matt)| re-fetch (curl)      | NOT vendored — `bootstrap.sh` pulls latest from GitHub |
| `~/learning/` content| iCloud + symlink     | iCloud Drive `learning/` ← `~/learning` symlink     |

`/teach` is Matt Pocock's in-progress skill — re-fetched fresh each bootstrap so it never
drifts from upstream. `~/learning/` holds learning workspaces (missions, HTML lessons, notes);
it lives in iCloud like the Obsidian vault.

## Multi-Mac setup

### Laptop (first time)
```bash
mkdir -p ~/Coding && cd ~/Coding
git clone git@github-personal:skozubek/claude-skills.git
bash ~/Coding/claude-skills/bootstrap.sh
```

### Daily sync
```bash
cd ~/Coding/claude-skills && git pull && bash bootstrap.sh
```
`bootstrap.sh` is idempotent — re-running only fixes missing links and re-fetches `teach`.

## Why iCloud is OK for `~/learning` but NOT for this repo

The git-in-iCloud failure mode (`.git/index` corruption, self-symlink loops *inside* an
iCloud dir) only bites **git repos** and **symlinks living inside iCloud**. `~/learning` is
plain content with no `.git`, and its symlink lives in `$HOME` pointing *into* iCloud — neither
pitfall applies. This repo stays git-only.

## Adding a new skill

1. Create `~/Coding/claude-skills/<skill-name>/` with `SKILL.md`
2. Add a `link` line to `bootstrap.sh`
3. Commit + push, then run `bootstrap.sh` on each Mac after pull
