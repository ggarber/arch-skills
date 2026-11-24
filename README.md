# arch-skills

Agent skills for documenting and reviewing software architecture.

## Skills

### `architecture-map`

Generates a self-contained HTML file that maps every service in a codebase and reviews its risks:

- **Home page:** a diagram of every service and its dependencies, with caller → callee arrows (hover a node to highlight its traffic, click to open its page), and a risk summary table per service and level (High, Medium, Low, Total) followed by cross-cutting themes.
- **One page per service:** a context diagram with the service in the middle, outputs on the left, inputs on the right and databases and queues below; its input and output interfaces in two columns, with scheduled jobs under the inputs; and its risks with level and categories.
- **Risk review:** each finding is verified in committed code, cites `file:line`, and is rated by severity (High, Medium, Low) and category (Reliability, Observability, Maintainability, Security, Bugs, Scalability). The review covers in-memory state that blocks zero-downtime upgrades, removal candidates, security and auth, performance, and coupling.

The agent writes one JSON data file and `scripts/build.py` validates it and renders the page from a fixed template, so maps look the same across projects and can be regenerated when the code changes. The page has no build step or server: open it in a browser, commit it to `docs/`, or publish it as a static file. It supports light and dark mode and phone widths.

Try it with a prompt such as:

> Create an architecture map of this repo with risks for every service.

To see the output without running the agent:

```bash
python3 skills/architecture-map/scripts/build.py \
  skills/architecture-map/assets/example-data.json example.html
open example.html
```

## Install

### Claude Code (plugin)

```
/plugin marketplace add ggarber/arch-skills
/plugin install arch-skills@arch-skills
```

The skill then loads automatically when you ask for an architecture map or review.

### Claude Code (skill only)

```bash
git clone https://github.com/ggarber/arch-skills
cp -r arch-skills/skills/architecture-map ~/.claude/skills/        # all projects
# or
cp -r arch-skills/skills/architecture-map .claude/skills/          # one project
```

### Other agents

The skill follows the [Agent Skills](https://agentskills.io) format (a folder with `SKILL.md`, scripts and references), so any agent that supports it can use it.

With the `skills` CLI, which installs into Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and other agents:

```bash
npx skills add ggarber/arch-skills
```

Or copy the folder into the agent's skills directory, for example `~/.codex/skills/` for OpenAI Codex or `.agents/skills/` in a repository.

Agents without skill support can still use it: point them at `skills/architecture-map/SKILL.md` and ask them to follow it.

## Requirements

- Python 3.8+ for `build.py` (standard library only).
- A browser to view the page. The page loads IBM Plex from Google Fonts and falls back to system fonts offline.

## Layout

```
.claude-plugin/
  plugin.json            Claude Code plugin manifest
  marketplace.json       lets this repo be added as a plugin marketplace
skills/architecture-map/
  SKILL.md               workflow and rules for the agent
  references/            data format and risk review rubric
  assets/template.html   page renderer (data injected at /*DATA*/)
  assets/example-data.json
  scripts/build.py       validates the data and writes the page
```

## License

MIT
