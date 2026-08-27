#!/usr/bin/env python3
"""RDA pack validator -- checks every SKILL.md against the Agent Skills standard and the RDA contract.

Checks: frontmatter presence and required keys; name matches directory; name charset and 64-char limit;
description non-empty, single-line, within the portability budget; required H2 sections present and ordered;
body size; dependency references resolve; kernel inheritance note present; no banned patterns
(numeric self-confidence, person-day estimates, fabricated-metric templates).

Also reports the aggregate metadata budget, because agent hosts load every skill's name+description at
startup and at least one host truncates the skill list once it exceeds ~8,000 characters. Against a full
pack it additionally verifies that every profile in install.sh is closed under the dependency graph.

Usage: python3 validate_pack.py [skills_dir] [--max-desc 200] [--max-lines 160] [--profiles install.sh]
"""
import argparse, os, re, sys

REQUIRED_FM = ["name", "description", "version", "license"]
REQUIRED_SECTIONS = ["Purpose","Business value","When to use","When NOT to use","Inputs","Procedure","Outputs",
    "Evidence requirements","Fact vs inference rules","Confidence scoring rules","Repository coverage rules",
    "Large repository strategy","Failure conditions","Escalation conditions","External validation required",
    "Known limitations","Success criteria","Example prompts"]
KERNEL = {"rda-00-audit-core", "rda-01-audit-orchestrator", "rda-02-repo-census"}
# RDA-00 is a contract document, not a procedure skill: it defines the banned patterns it must quote,
# and it deliberately has no Procedure/Coverage sections because it never executes alone.
CONTRACT_EXEMPT = {"rda-00-audit-core"}
# P4 is split into two sequential sessions on hosts with a small skill-list budget. P4B runs second, so
# it may rely on artifacts P4A already wrote; the reverse would be a forward dependency and is a defect.
PHASE_PREDECESSOR = {"P4B": "P4A"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BANNED = [
    (re.compile(r"confidence\W{0,3}(0?\.\d+|\d{1,3}\s?%)", re.I), "numeric self-confidence (banned by CC-1 s0)"),
    (re.compile(r"\b\d+(\.\d+)?\s*(person|engineer|dev)[- ](days?|hours?)\b", re.I), "person-day point estimate (BSR-10)"),
    (re.compile(r"\b(accuracy|precision|recall|compliance)\s*[:>]\s*\d{1,3}\s?%", re.I), "hardcoded fabricated metric template"),
]

def parse_fm(text):
    if not text.startswith("---"): return None, text
    end = text.find("\n---", 3)
    if end == -1: return None, text
    raw, body = text[3:end], text[end+4:]
    fm, cur_key = {}, None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"): continue
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m and not line.startswith(" "):
            cur_key = m.group(1); fm[cur_key] = m.group(2).strip()
        elif line.startswith("  ") and cur_key:
            fm.setdefault("_nested_" + cur_key, []).append(line.strip())
    return fm, body

def parse_profiles(path):
    """Read profile -> skill-id list out of install.sh's case block.

    install.sh is the single source of truth for profile membership (generate_adapters.py mirrors it),
    so the closure check reads it directly rather than keeping a third copy that can drift.
    """
    if not path or not os.path.exists(path): return {}
    out = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r'\s*(P[0-9A-Z]+)\)\s*IDS="([^"]*)"', line)
        if m: out[m.group(1)] = m.group(2).strip()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skills_dir", nargs="?", default="skills")
    ap.add_argument("--max-desc", type=int, default=200)
    ap.add_argument("--max-lines", type=int, default=160)
    ap.add_argument("--profiles", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "install.sh"),
                    help="install.sh to read profile membership from for the closure check")
    ap.add_argument("--budgets", action="store_true", help="print the per-profile startup metadata budget table")
    a = ap.parse_args()

    problems, meta_budget, seen, deps, texts, fanin, per_skill = [], 0, {}, {}, {}, set(), {}
    dirs = sorted(d for d in os.listdir(a.skills_dir) if os.path.isdir(os.path.join(a.skills_dir, d)))
    for d in dirs:
        p = os.path.join(a.skills_dir, d, "SKILL.md")
        if not os.path.exists(p):
            problems.append((d, "E100", "no SKILL.md")); continue
        text = open(p, encoding="utf-8").read()
        texts[d] = text
        fm, body = parse_fm(text)
        if fm is None:
            problems.append((d, "E101", "missing YAML frontmatter")); continue
        for k in REQUIRED_FM:
            if k not in fm: problems.append((d, "E102", f"frontmatter missing '{k}'"))
        name = fm.get("name", "")
        if name != d: problems.append((d, "E103", f"name '{name}' != directory '{d}'"))
        if not NAME_RE.match(name): problems.append((d, "E104", f"name '{name}' invalid charset (lowercase/digits/single hyphens)"))
        if len(name) > 64: problems.append((d, "E105", "name exceeds 64 characters"))
        desc = fm.get("description", "")
        if not desc: problems.append((d, "E106", "empty description"))
        if len(desc) > a.max_desc:
            problems.append((d, "E107", f"description {len(desc)} chars > {a.max_desc} (portability budget)"))
        if len(desc) > 1024: problems.append((d, "E108", "description exceeds the 1024-char spec limit"))
        # The host loads name + description + a reference to the skill file. Measure the path in its
        # location-independent form: including the absolute path made the same pack report a different
        # budget depending on where it was installed, so the figures quoted in docs never matched what
        # a user saw after `install.sh`.
        entry = len(name) + len(desc) + len(f"{d}/SKILL.md") + 4
        meta_budget += entry
        rid = re.search(r'rda_id:\s*"?(RDA-\d\d)', text)
        if rid: per_skill[rid.group(1)] = entry
        seen[d] = fm

        heads = re.findall(r"^## (.+)$", body, re.M)
        for s in ([] if d in CONTRACT_EXEMPT else REQUIRED_SECTIONS):
            if s not in heads: problems.append((d, "E110", f"missing section '## {s}'"))
        idx = [heads.index(s) for s in REQUIRED_SECTIONS if s in heads]
        if idx != sorted(idx): problems.append((d, "E111", "required sections are out of order"))
        n_lines = text.count("\n")
        if n_lines > a.max_lines: problems.append((d, "E112", f"{n_lines} lines > {a.max_lines} (context budget)"))
        if n_lines < 40: problems.append((d, "E113", f"{n_lines} lines -- too thin to be implementation-ready"))
        if d not in KERNEL and "RDA-00" not in body[:1200] and "Inherits" not in body[:1200]:
            problems.append((d, "E114", "no kernel inheritance note near the top"))
        for rx, why in ([] if d in CONTRACT_EXEMPT else BANNED):
            if rx.search(body): problems.append((d, "E120", f"banned pattern: {why}"))
        m = re.search(r"depends_on:\s*\"?([^\"\n]*)\"?", text)
        if m:
            raw = m.group(1)
            # A range (RDA-03..RDA-30) or the literal "all" marks a fan-in aggregator: it consumes
            # whatever upstream findings exist rather than requiring each one, so it does not
            # constrain profile closure. Explicit enumerations are hard dependencies and do.
            if ".." in raw or re.search(r"\ball\b", raw, re.I): fanin.add(d)
            for lo, hi in re.findall(r"RDA-(\d\d)\s*\.\.\s*RDA-(\d\d)", raw):
                raw = raw.replace(f"RDA-{lo}..RDA-{hi}", " ".join(f"RDA-{i:02d}" for i in range(int(lo), int(hi) + 1)))
                raw = raw.replace(f"RDA-{lo} .. RDA-{hi}", " ".join(f"RDA-{i:02d}" for i in range(int(lo), int(hi) + 1)))
            deps[d] = [x.strip() for x in raw.replace(",", " ").split()
                       if x.strip() and x.strip().startswith("RDA-")]

    KNOWN = {f"RDA-{i:02d}" for i in range(0, 38)}
    installed, id_of = set(), {}
    for d in seen:
        # Reuse the already-parsed text rather than re-reading; the earlier bug re-opened the file
        # without an explicit encoding, which decodes under the locale codepage on Windows.
        m = re.search(r'rda_id:\s*"?(RDA-\d\d)', texts[d])
        if m: installed.add(m.group(1)); id_of[d] = m.group(1)
    warnings = []
    for d, dl in deps.items():
        for dep in dl:
            if not dep.startswith("RDA-"): continue
            if dep not in KNOWN:
                problems.append((d, "E130", f"depends_on unknown skill '{dep}' (outside RDA-00..RDA-37)"))
            elif dep not in installed:
                warnings.append((d, "W131", f"depends_on '{dep}' which is not in this install -- expected for a "
                                            f"profile install, a defect for a full pack"))

    # Profile dependency closure. PROFILES.md claims every profile is closed under the dependency graph;
    # nothing checked it, and P4A shipped depending on RDA-19, a skill scheduled in the later P4B phase --
    # a forward dependency no persisted artifact can satisfy. Only meaningful against a full pack, since
    # a narrowed install cannot see the skills it omits.
    if len(installed) == len(KNOWN):
        hard = {id_of[d]: set(dl) for d, dl in deps.items() if d in id_of and d not in fanin}
        profs = parse_profiles(a.profiles)
        for prof, ids in sorted(profs.items()):
            members = set(KNOWN) if ids == "ALL" else {f"RDA-{i}" for i in ids.split()}
            unknown = members - KNOWN
            if unknown:
                problems.append((f"profile:{prof}", "E141", f"lists unknown skill(s) {sorted(unknown)}"))
            # P4B is the second half of a sequential split, so P4A's artifacts are already on disk when
            # it runs. Every other profile must stand alone.
            avail = members | ({f"RDA-{i}" for i in profs.get(PHASE_PREDECESSOR[prof], "").split()}
                               if prof in PHASE_PREDECESSOR else set())
            for sk in sorted(members & KNOWN):
                for dep in sorted(hard.get(sk, set()) - avail):
                    problems.append((f"profile:{prof}", "E140",
                                     f"{sk} depends on {dep}, which the profile omits (not dependency-closed)"))

    for d, code, msg in problems: print(f"[{code}] {d}: {msg}")
    for d, code, msg in warnings: print(f"[{code}] {d}: {msg}")
    print(f"\nskills={len(dirs)} problems={len(problems)}")
    print(f"startup_metadata_budget={meta_budget} chars"
          f"  ({'OK' if meta_budget <= 8000 else 'OVER the ~8000-char host cap: install per profile, not all at once'})")
    if a.budgets:
        # PROFILES.md quotes per-profile budgets. Print them here so the doc can be checked against the
        # pack instead of hand-maintained -- the numbers it originally shipped had drifted.
        print("\nper-profile startup metadata budget:")
        for prof, ids in sorted(parse_profiles(a.profiles).items()):
            ms = sorted(installed) if ids == "ALL" else [f"RDA-{i}" for i in ids.split()]
            tot = sum(per_skill.get(m, 0) for m in ms)
            print(f"  {prof:4} skills={len(ms):2}  budget={tot:6,} chars  {'OK' if tot <= 8000 else 'OVER'}")
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
