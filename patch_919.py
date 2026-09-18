# -*- coding: utf-8 -*-
# Mo's Feed daily patch — 2026-09-19 (v11.5, 10 channels / 32 cards)
import io, json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "index.html")

CARDS = json.load(io.open(os.path.join(HERE, "cards_919.json"), encoding="utf-8"))

DISCUSS_PROMPT = io.open(os.path.join(HERE, "prompt_919.txt"), encoding="utf-8").read().strip()

src = io.open(PATH, encoding="utf-8").read()

lines = src.split("\n")
start = None
end = None
for i, ln in enumerate(lines):
    if ln.startswith("const CARDS = ["):
        start = i
    elif start is not None and ln.startswith("];"):
        end = i
        break
assert start is not None and end is not None, "CARDS block not found"

body = []
body.append("const CARDS = [")
for c in CARDS:
    body.append("    " + json.dumps(c, ensure_ascii=False) + ",")
body.append("];")

lines[start:end + 1] = body
src = "\n".join(lines)

# DISCUSS_PROMPT
src2 = re.sub(r'const DISCUSS_PROMPT = "(?:[^"\\]|\\.)*";',
              lambda m: "const DISCUSS_PROMPT = " + json.dumps(DISCUSS_PROMPT, ensure_ascii=False) + ";",
              src, count=1)
assert re.search(r'const DISCUSS_PROMPT = "', src), "DISCUSS_PROMPT not found"
src = src2

# header date + version
src2 = src.replace("updated 09/18/2026", "updated 09/19/2026").replace(">v11.3<", ">v11.5<").replace(">v11.4<", ">v11.5<")
assert "updated 09/19/2026" in src2, "header not replaced"
assert "v11.5" in src2
src = src2

io.open(PATH, "w", encoding="utf-8", newline="\n").write(src)
print("cards:", len(CARDS))
