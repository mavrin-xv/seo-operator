"""Shared helpers for the seo-operator scripts. Standard library only.

State lives in one folder per site:

    <state>/<site>/config.json, gsc/, health/, candidates/, reports/,
    runs.jsonl, outcomes.jsonl, truth.md, radar.md, needs-you.md

<state> comes from --state, then the SEO_STATE_DIR environment variable,
then ./.seo in the current folder. Nothing is pinned to where the scripts live.
"""
import datetime
import json
import os
import sys

DEFAULT_THRESHOLDS = {
    "ttfb_ms": 800,          # time to first byte budget per page
    "html_kb": 250,          # raw HTML weight budget per page
    "min_impressions": 50,   # below this a CTR gap is noise
    "strike_position": [4, 20],
    "ctr_max_position": 15,  # below this rank sets CTR, not the snippet
    "cooldown_days": 60,     # a target acted on is off the board this long
    "verify_min_days": 21,
    "prune_days": 90,
}

# Expected organic CTR by average position. A conservative blend of public
# position-CTR studies (see references/scoring.md); linear between anchors.
CTR_CURVE = [(1, .28), (2, .15), (3, .10), (4, .073), (5, .053), (6, .040),
             (7, .032), (8, .026), (9, .022), (10, .019), (15, .011),
             (20, .007), (30, .003), (50, .001)]


def utf8_stdout():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def expected_ctr(pos):
    if pos is None:
        return 0.0
    if pos <= CTR_CURVE[0][0]:
        return CTR_CURVE[0][1]
    for (p1, c1), (p2, c2) in zip(CTR_CURVE, CTR_CURVE[1:]):
        if p1 <= pos <= p2:
            return c1 + (c2 - c1) * (pos - p1) / (p2 - p1)
    return CTR_CURVE[-1][1]


def state_root(arg=None):
    return os.path.abspath(arg or os.environ.get("SEO_STATE_DIR") or os.path.join(os.getcwd(), ".seo"))


def site_dir(root, site, must_exist=True):
    d = os.path.join(root, site)
    if must_exist and not os.path.isdir(d):
        sys.exit("no state for site '%s' in %s. Run: seo_state.py init %s --domain example.com"
                 % (site, root, site))
    return d


def load_config(root, site):
    p = os.path.join(site_dir(root, site), "config.json")
    if not os.path.exists(p):
        sys.exit("missing %s. Run seo_state.py init first." % p)
    with open(p, encoding="utf-8") as fh:
        cfg = json.load(fh)
    th = dict(DEFAULT_THRESHOLDS)
    th.update(cfg.get("thresholds") or {})
    cfg["thresholds"] = th
    return cfg


def snapshots(root, site, kind):
    """All snapshots of a kind, oldest first, as (stem, data)."""
    d = os.path.join(site_dir(root, site), kind)
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                out.append((f[:-5], json.load(fh)))
    return out


def latest(root, site, kind):
    s = snapshots(root, site, kind)
    return s[-1] if s else (None, None)


def load_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                print("warn: %s line %d is not JSON, skipped" % (path, n), file=sys.stderr)
    return out


def append_jsonl(path, rec):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def today(arg=None):
    return datetime.date.fromisoformat(arg) if arg else datetime.date.today()


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
