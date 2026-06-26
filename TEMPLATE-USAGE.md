# How this tracker works

This repository is a **competition tracker**: the home for context about one
competition, including deadlines, deliverables, links, and the team's writeup.
The actual **code lives in a separate repository**, linked under `links.code`.

## The one rule

**Edit `competition.yml`. Never hand-edit the AUTO block in `README.md`.**

`competition.yml` is the single source of truth. A GitHub Action runs
`scripts/render.py` on every push and once a day. It regenerates only the region
between `<!-- AUTO:START -->` and `<!-- AUTO:END -->`:

- a generated hero with status and a live countdown to the next deadline
- a Mermaid timeline
- an animated progress bar and the deliverables checklist
- the resources table

Everything outside that block (Problem statement, Approach, Demo, Notes,
Results) is your **free-form canvas**. Write whatever you like there; the
automation never touches it.

## Create a new competition

From the organization tooling in the `.github` repo:

```powershell
./ops/new-competition.ps1 -Name "AI Innovation Challenge" -Repo "aiic-compfest18" -Organizer "COMPFEST 18" -WithCode
```

This creates a repo from this template, tags it with the `competition` topic so
the org dashboard finds it, and optionally creates a private code repository.
Then fill in `competition.yml`.

## Render locally (optional)

```bash
pip install pyyaml
python scripts/render.py
```

## Theming

Set `theme.accent` (a hex value without `#`) to color the hero, the accent rule,
the status pill, and the progress bar. Set `theme.banner` to a custom image to
replace the generated hero entirely.

## Discovery

The org dashboard finds trackers by the `competition` topic, not by name, so you
can name repositories however you like. Keep the topic on.
