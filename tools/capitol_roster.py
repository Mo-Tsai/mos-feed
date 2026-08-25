#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""產出「政要績效」分頁的個別議員資料 (const CAPITOL_ROSTER)。

資料來源是眾議院書記官的官方申報索引與 PTR PDF，免 API key、無流量限制：
  索引  https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.ZIP
  PDF   https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{YEAR}/{DocID}.pdf

這兩個網址都沒有 CORS 標頭，瀏覽器端抓不到，所以資料必須先在這裡算好、
再烘進 index.html。PDF 會快取在 tools/.capitol_cache/，每天只有 2-5 筆新申報
需要下載。

DocID 為 8 碼且以 20 開頭者是線上申報、可直接抽文字（約佔 88%）；
7 碼的是紙本掃描件，抽不出文字，本工具直接跳過並計入 skipped_scanned。

用法：
    python tools/capitol_roster.py            # 印出 JSON 到 stdout
    python tools/capitol_roster.py --days 90  # 只算近 90 天的申報（預設）
    python tools/capitol_roster.py --write    # 直接改寫 index.html 的 CAPITOL_ROSTER
"""

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".capitol_cache")
INDEX_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP"
PDF_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc}.pdf"
UA = "Mozilla/5.0 (compatible; MosFeed/1.0; +https://mo-tsai.github.io/mos-feed/)"

# PTR 內文的一列交易，例如：
#   Alphabet Inc. - Class A Common Stock (GOOGL) [ST]  P 06/29/2026 06/29/2026 $1,001 - $15,000
TRADE_RE = re.compile(
    r"\(([A-Z][A-Z.\-]{0,5})\)\s*\[(ST|OP|ОР|STO|OT|PS|EF|CS)\]"   # 代號 + 資產類別
    r"(?:\s*\(partial\))?\s*"
    r"\b([PSE])\b[a-z\s]*"                                          # P=買 S=賣 E=交換
    r"(\d{2}/\d{2}/\d{4})\s*"                                       # 成交日
    r"(\d{2}/\d{2}/\d{4})\s*"                                       # 申報通知日
    r"\$([\d,]+)\s*-\s*\$([\d,]+)",                                 # 金額區間
    re.IGNORECASE,
)

# 申報只給區間不給數字，而且絕大多數落在最低的 $1,001-$15,000 級距。
# 只加總下緣會得到「筆數 × 1001」這種假精確的數字，所以上下緣都留著，
# 前端一律顯示成區間，不要當成實際金額。
def _amt(s):
    try:
        return int(s.replace(",", ""))
    except ValueError:
        return 0


# First 欄位常混進敬稱，例如 "Richard Dean Dr"
_HONORIFIC = re.compile(r"\b(Dr|Mr|Mrs|Ms|Hon|Rep|Sen)\.?\b", re.IGNORECASE)


def _clean_name(first, last):
    first = _HONORIFIC.sub("", first)
    return " ".join(("%s %s" % (first, last)).split())


def fetch(url, binary=True):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode("utf-8", "replace")


def load_index(year):
    """回傳 [(filing_date, doc_id, first, last, state_dst), ...]，只含 PTR。"""
    raw = fetch(INDEX_URL.format(year=year))
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".xml"))
        xml = z.read(name)
    root = ET.fromstring(xml)
    out = []
    for m in root.findall("Member"):
        get = lambda k: (m.findtext(k) or "").strip()
        if get("FilingType") != "P":
            continue
        try:
            date = dt.datetime.strptime(get("FilingDate"), "%m/%d/%Y").date()
        except ValueError:
            continue
        out.append((date, get("DocID"), get("First"), get("Last"), get("StateDst")))
    return out


def pdf_text(year, doc):
    """抓 PTR PDF 並抽第一層文字；掃描件回傳空字串。"""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, doc + ".pdf")
    if not os.path.exists(path):
        try:
            data = fetch(PDF_URL.format(year=year, doc=doc))
        except Exception as e:
            sys.stderr.write("fetch fail %s: %s\n" % (doc, e))
            return ""
        with open(path, "wb") as f:
            f.write(data)
    try:
        import pypdf
    except ImportError:
        sys.stderr.write("need pypdf: pip install pypdf\n")
        raise
    try:
        reader = pypdf.PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        sys.stderr.write("parse fail %s: %s\n" % (doc, e))
        return ""


def build(year, days, top):
    today = dt.date.today()
    filings = [f for f in load_index(year) if (today - f[0]).days <= days]
    filings.sort(key=lambda x: x[0])

    people = defaultdict(lambda: {
        "trades": 0, "buys": 0, "sells": 0, "lo_total": 0, "hi_total": 0,
        "tickers": defaultdict(int), "order": {}, "last": None, "doc": None,
    })
    scanned = 0

    for date, doc, first, last, state in filings:
        # 7 碼 DocID 是紙本掃描件，抽不出文字，跳過
        if not (len(doc) == 8 and doc.startswith("20")):
            scanned += 1
            continue
        text = pdf_text(year, doc)
        if not text.strip():
            scanned += 1
            continue
        key = (last, first, state)
        p = people[key]
        for tic, _cls, act, _tdate, _ndate, lo, hi in TRADE_RE.findall(text):
            p["trades"] += 1
            act = act.upper()
            if act == "P":
                p["buys"] += 1
            elif act == "S":
                p["sells"] += 1
            p["lo_total"] += _amt(lo)
            p["hi_total"] += _amt(hi)
            tic = tic.upper()
            p["tickers"][tic] += 1
            p["order"].setdefault(tic, len(p["order"]))
        if p["trades"]:
            iso = date.isoformat()
            if p["last"] is None or iso > p["last"]:
                p["last"] = iso
                p["doc"] = doc

    roster = []
    for (last, first, state), p in people.items():
        if not p["trades"]:
            continue
        # 同票數時用「在申報書中首次出現的順序」打破平手，不要退回字母序
        # （字母序會讓 A、ADBE、AEE 這種毫無意義的組合浮上來）
        tops = sorted(p["tickers"].items(),
                      key=lambda kv: (-kv[1], p["order"][kv[0]]))[:4]
        roster.append({
            "name": _clean_name(first, last),
            "dst": state,
            "n": p["trades"],
            "buy": p["buys"],
            "sell": p["sells"],
            "lo": p["lo_total"],            # 申報區間下緣加總
            "hi": p["hi_total"],            # 申報區間上緣加總
            "distinct": len(p["tickers"]),
            "top": [t for t, _ in tops],
            "last": p["last"],
            "url": PDF_URL.format(year=year, doc=p["doc"]),
        })
    roster.sort(key=lambda r: (-r["n"], r["name"]))

    return {
        "updated": today.isoformat(),
        "window": days,
        "source": "https://disclosures-clerk.house.gov/FinancialDisclosure",
        "filings": len(filings),
        "skipped_scanned": scanned,
        "roster": roster[:top],
    }


def write_into_html(payload, html_path):
    marker = "const CAPITOL_ROSTER = "
    with io.open(html_path, encoding="utf-8") as f:
        src = f.read()
    blob = marker + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";"
    if marker not in src:
        raise SystemExit("index.html 裡找不到 %s，請先加上該常數" % marker)
    start = src.index(marker)
    end = src.index("\n", start)
    src = src[:start] + blob + src[end:]
    with io.open(html_path, "w", encoding="utf-8") as f:
        f.write(src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=dt.date.today().year)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--write", action="store_true", help="直接改寫 index.html")
    args = ap.parse_args()

    payload = build(args.year, args.days, args.top)

    if args.write:
        html = os.path.join(os.path.dirname(HERE), "index.html")
        write_into_html(payload, html)
        sys.stderr.write("wrote %d members into %s\n" % (len(payload["roster"]), html))
    else:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
