# claude-skills

Private monorepo for custom Claude Code skills that live globally in `~/.claude/skills/` via symlink.

## Layout

```
claude-skills/
└── wiki-compile/        # Karpathy-style LLM wiki compiler (global skill)
    ├── SKILL.md
    └── templates/       # project scaffold for /wiki-compile init
```

## Multi-Mac setup

### Main Mac (first time)
```bash
cd ~/Coding/claude-skills/wiki-compile
# already cloned, already symlinked
ls -la ~/.claude/skills/wiki-compile   # should point here
```

### Laptop (first time)
```bash
mkdir -p ~/Coding
cd ~/Coding
git clone git@github.com:skozubek/claude-skills.git
ln -s ~/Coding/claude-skills/wiki-compile ~/.claude/skills/wiki-compile
```

### Daily sync
```bash
cd ~/Coding/claude-skills && git pull
```

## Why not iCloud

iCloud sync + git repo causes `.git/index` corruption (known issue). Self-symlink loops can appear inside iCloud-synced dirs. Git + GitHub is the clean multi-Mac sync mechanism.

## Adding a new skill

1. Create `~/Coding/claude-skills/<skill-name>/` with `SKILL.md`
2. `ln -s ~/Coding/claude-skills/<skill-name> ~/.claude/skills/<skill-name>`
3. Commit + push
4. Repeat symlink on other Macs after pull
