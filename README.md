# Zwift Coach

A personal cycling coach for [Claude Code](https://claude.com/claude-code). It reads your [Intervals.icu](https://intervals.icu) data, schedules structured workouts that sync to Zwift, and publishes a training calendar.

**Live plan:** https://complex-ping.github.io/zwift-coach/

## What's here

| Path | Purpose |
|---|---|
| `skills/zwift-coach/` | The coaching skill: workflows, training model, Zwift sync notes, plan generator |
| `agents/zwift-coach.md` | A coach agent that uses the skill |
| `athlete.json` | Your FTP, max HR, ride days, weekly targets |
| `index.html`, `data.json` | The calendar page and the data it shows |
| `install.sh` | Copies the skill and agent into `~/.claude` |
| `connect-intervals.sh` | Registers the Intervals.icu MCP server with your key |

## Setup

### 1. Install the skill and agent

```bash
./install.sh
```

### 2. Connect Intervals.icu

Create an API key at [intervals.icu/settings](https://intervals.icu/settings) under **Developer**. Your athlete ID is in your profile URL and looks like `i123456`. Run this in a terminal and enter both when prompted:

```bash
./connect-intervals.sh
```

Claude Code stores the key in your local config. Never commit it.

### 3. Connect Zwift

In Intervals.icu settings, open the Zwift box and choose **Connect**. Set the same FTP in Zwift and Intervals.icu.

### 4. See ride charts on the page

Open the page and choose **Connect Intervals**, then paste your API key. Clicking a finished ride then loads its power, heart rate and cadence live from Intervals. The key stays in that browser's storage and only goes to intervals.icu. It gives full access to your Intervals account, so use it only on your own devices, and choose **Disconnect** when you're done on a shared one.

## Use it

```text
/zwift-coach what's my next ride and why?
/zwift-coach move Saturday's ride to Monday
/zwift-coach review this week
```

## Change the plan

Edit `WEEKS` in `skills/zwift-coach/scripts/build_plan.py` and your details in `athlete.json`, then check the plan against your weekly targets:

```bash
python3 -I skills/zwift-coach/scripts/build_plan.py --athlete athlete.json --out-events events.json --out-page data.json
```

## Credits

Ideas and approach drew on these projects. No code was copied from them unless noted:

- [hhopke/intervals-icu-mcp](https://github.com/hhopke/intervals-icu-mcp) (MIT): the MCP server this coach uses
- [jsattler/claude-plugins](https://github.com/jsattler/claude-plugins) (MIT): coaching philosophy and workflow structure
- [estruyf/skill-cycling-plan-coach](https://github.com/estruyf/skill-cycling-plan-coach) (MIT): rotation and weekly constraints
- [disco-trooper/skills](https://github.com/disco-trooper/skills) (MIT): periodization references
- [makslesz/intervals](https://github.com/makslesz/intervals): `index.html` is copied from this project with the author's permission

Not medical advice. Check with a doctor before hard training if you have any health concerns.

## License

MIT, except `index.html`, which belongs to its author at [makslesz/intervals](https://github.com/makslesz/intervals) and is used here with permission.
