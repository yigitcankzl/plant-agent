"""Every recorded engineering-loop run, by case: how many ended done, how they stopped, what they cost. No model call."""
import collections, glob, json, sys


def runs(root="runs/ws"):
    for f in sorted(glob.glob(f"{root}/*/work/*/worklog.json")):
        try:
            w = json.load(open(f))
        except (OSError, ValueError):
            continue
        status = w.get("status")
        if status == "running":
            status = "interrupted"  # ponytail: a run still marked running after the fact was killed
        yield f.split("/")[-4], f.split("/")[-2], status, w.get("usd_total") or 0, len(w.get("rounds") or []), w.get("model") or "muse-wonder-1.0"


def table(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[r[0]].append(r)
    out = ["| Case | Runs | Done | How the others stopped | Spend |", "|---|---:|---:|---|---:|"]
    for case, rs in by.items():
        other = collections.Counter(r[2] for r in rs if r[2] != "done")
        out.append(f"| {case} | {len(rs)} | {sum(r[2] == 'done' for r in rs)} | "
                   f"{', '.join(f'{k} {v}' for k, v in other.items()) or '-'} | ${sum(r[3] for r in rs):.2f} |")
    alls = [r for rs in by.values() for r in rs]
    out.append(f"| **All** | {len(alls)} | {sum(r[2] == 'done' for r in alls)} | | ${sum(r[3] for r in alls):.2f} |")
    return "\n".join(out)


if __name__ == "__main__":
    rows = list(runs(*sys.argv[1:]))
    assert all(len(r) == 6 for r in rows)
    print(table(rows))
