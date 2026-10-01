"""Rewrite the Open source list in README.md between the OPEN-SOURCE markers
with the pull requests jonboy648 has had merged into other people's projects.

Reads search results from `gh api` (JSON on stdin):
    gh api "search/issues?q=is:pr+author:jonboy648+is:merged+is:public+-user:jonboy648+-user:VarietyVaultLLC&sort=updated&per_page=10" \
        | python scripts/open_source.py README.md
"""
import json
import re
import sys

START, END = "<!-- OPEN-SOURCE:START -->", "<!-- OPEN-SOURCE:END -->"
# Our own account and org never count as "other people's projects", and their
# private repos must never be named on a public page, whatever the token can see.
OWN = {"jonboy648", "varietyvaultllc"}
RELEASES = ["- **[printed-contributions](https://github.com/jonboy648/printed-contributions)**: a GitHub Action that draws your contribution year as a 3D print, like the one above"]


def lines_for(items):
    out = list(RELEASES)
    for it in items:
        repo = it["repository_url"].split("/repos/", 1)[1]
        if repo.split("/")[0].lower() in OWN:
            continue
        title = it["title"].replace("[", "(").replace("]", ")")
        out.append(f"- **{repo}**: [{title}]({it['html_url']})")
    if len(out) == len(RELEASES):
        out.append("- First merged pull request to another project: coming up")
    return out


def rewrite(readme, items):
    block = "\n".join([START, *lines_for(items), END])
    new, n = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda m: block, readme, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("README.md has no OPEN-SOURCE markers")
    return new


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # self-check: markers are replaced, and PR rows are built from search results
        demo = f"a\n{START}\nold\n{END}\nb"
        got = rewrite(demo, [{"repository_url": "https://api.github.com/repos/SoftFever/OrcaSlicer",
                              "title": "Fix [bed] mesh", "html_url": "https://github.com/SoftFever/OrcaSlicer/pull/1"}])
        assert "old" not in got and "**SoftFever/OrcaSlicer**: [Fix (bed) mesh]" in got and got.startswith("a\n")
        assert "coming up" in rewrite(demo, [])
        own = [{"repository_url": "https://api.github.com/repos/VarietyVaultLLC/Segue", "title": "x", "html_url": "u"}]
        assert "Segue" not in rewrite(demo, own)
        print("self-check ok")
    else:
        path = sys.argv[1]
        items = json.load(sys.stdin).get("items", [])
        text = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8").write(rewrite(text, items))
