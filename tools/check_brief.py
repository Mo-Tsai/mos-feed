#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mo's Feed 每日晨報上線前檢查。

用法:
    python tools/check_brief.py                  # 檢查 index.html
    python tools/check_brief.py --rebuild-baseline   # 從 git 歷史重建用字基準

離開碼:
    0  全部通過,可以 commit
    1  硬性錯誤(結構壞掉、簡體字、日文漢字)—— 一定要修
    2  有待確認的罕用字 —— 逐一看過上下文,是錯字就修,
       確認沒問題就把該字加進 tools/zh_allow.txt 再跑一次

設計說明:
    字元層級的檢查只抓得到「罕用字被誤用」(諠/惄/綼/尜/獼…),
    抓不到「常用字放錯位置」(陡峭→陳峭、頻道→額道、濫用→濾用),
    因為那些字本身在別處是合法的。後者只能靠人或模型讀過一遍。
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'index.html')
BASELINE = os.path.join(ROOT, 'tools', 'zh_baseline.txt')
ALLOW = os.path.join(ROOT, 'tools', 'zh_allow.txt')

# 9 頻道 30 卡(CLAUDE.md 規格)
CHANNELS = {
    '隔夜盤勢': 4, '財報速報': 3, '總經政策': 3, '產業風向': 3, '小型股風雲': 5,
    '忽視雷達': 6, '內部人動向': 3, '本週事件': 2, '今日評估': 1,
}
REQUIRED = ('id', 'channel', 'tag', 'color', 'en', 'zh', 'url', 'stocks')

# 簡體字與日文新字體 —— 出現在繁體內文即為錯,無例外
BAD_CHARS = (
    '归辩产业发说读画乱权继续时对这来国会电经济学内医单旧脱担汎个们为长门问间关开东车马鸟鱼见贝页风飞'
    '讲话认识运动员两严丽举义乐买卖书图团园区协厂历压厌县参双变叠台叶号叹优伟传伤价众伙体余俩',
    '倾偿储儿党兰关兴养兽内冈军农冲决况冻净凉减凤办务动励劳势勋包医华协单卖卫却厉压厕厢厨县参',
)
BAD_SET = set(''.join(BAD_CHARS))
# 誤判防呆:這些字在繁體中文裡本來就合法,不可列為簡體字
BAD_SET -= set('业内单台区县参双台号台叶价体余包医华协卫却厉压厕厢厨')
# 明確要抓的日文新字體(繁體有對應正字)
BAD_SET |= set('国会学画来内医単旧脱担汎乱権読釈続黒産説変実経済帰発断円図対応価収営県体来観覚戦点')
BAD_SET -= set('体点')  # 這兩個在繁體語境已足夠常見,避免誤報


def load_html():
    with open(HTML, encoding='utf-8') as f:
        return f.read()


def extract_cards(src):
    """回傳 (cards, DISCUSS_PROMPT)。解析失敗丟 ValueError。"""
    lines = src.split('\n')
    starts = [i for i, l in enumerate(lines) if 'const CARDS' in l]
    if not starts:
        raise ValueError('找不到 const CARDS')
    st = starts[0]
    ends = [i for i, l in enumerate(lines) if i > st and l.strip().startswith('];')]
    if not ends:
        raise ValueError('找不到 CARDS 結尾的 "];"')
    raw = '[' + '\n'.join(lines[st:ends[0]]).split('= [', 1)[1]
    cards = json.loads(raw.rstrip().rstrip(',') + ']')
    m = re.search(r'const DISCUSS_PROMPT = (`|")(.*?)\1', src, re.S)
    return cards, (m.group(2) if m else '')


def zh_text(cards, prompt):
    """所有應為繁體中文的文字(不含 en 欄位)。"""
    parts = []
    for c in cards:
        parts.append(c.get('zh', ''))
        parts.append(c.get('tag', ''))
        parts.append(c.get('channel', ''))
        for s in c.get('stocks', []):
            parts.append(s.get('n', ''))
        if c.get('status'):
            parts.append(str(c['status']))
    parts.append(prompt)
    return '\n'.join(parts)


def cjk(text):
    return {ch for ch in text if '一' <= ch <= '鿿'}


def read_charfile(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding='utf-8') as f:
        return cjk(f.read())


def context_of(cards, prompt, ch, width=18):
    """回傳該字第一次出現的上下文,方便人判斷。"""
    for c in cards:
        for field in ('zh', 'tag'):
            v = c.get(field, '')
            if ch in v:
                i = v.index(ch)
                return f"[{c['id']}.{field}] …{v[max(0, i-width):i+width]}…"
        for s in c.get('stocks', []):
            v = s.get('n', '')
            if ch in v:
                i = v.index(ch)
                return f"[{c['id']}.{s.get('t','?')}] …{v[max(0, i-width):i+width]}…"
    if ch in prompt:
        i = prompt.index(ch)
        return f"[DISCUSS_PROMPT] …{prompt[max(0, i-width):i+width]}…"
    return '(找不到上下文)'


def rebuild_baseline(min_versions=2):
    """掃過 index.html 的所有歷史版本,取出現在 >= N 個版本的字當基準。"""
    out = subprocess.run(['git', 'log', '--format=%H', '--', 'index.html'],
                         cwd=ROOT, capture_output=True)
    revs = out.stdout.decode('utf-8', 'replace').strip().split('\n')
    freq = collections.Counter()
    parsed = 0
    for sha in revs:
        if not sha.strip():
            continue
        blob = subprocess.run(['git', 'show', f'{sha}:index.html'],
                              cwd=ROOT, capture_output=True)
        try:
            cards, prompt = extract_cards(blob.stdout.decode('utf-8', 'replace'))
        except Exception:
            continue
        parsed += 1
        for ch in cjk(zh_text(cards, prompt)):
            freq[ch] += 1
    keep = sorted(ch for ch, n in freq.items() if n >= min_versions)
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    with open(BASELINE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'# 由 tools/check_brief.py --rebuild-baseline 產生,勿手改。\n')
        f.write(f'# 取自 {parsed} 個歷史版本中出現於 >= {min_versions} 個版本的字。\n')
        for i in range(0, len(keep), 60):
            f.write(''.join(keep[i:i+60]) + '\n')
    print(f'基準已重建:掃過 {parsed} 個版本,收錄 {len(keep)} 個字 → {os.path.relpath(BASELINE, ROOT)}')


def check():
    errors, warns = [], []
    src = load_html()

    try:
        cards, prompt = extract_cards(src)
    except Exception as e:
        print(f'✗ CARDS 解析失敗:{e}')
        print('  頁面幾乎確定是白的,不要 commit。')
        return 1

    # ---- 結構 ----
    if len(cards) != 30:
        errors.append(f'卡片數為 {len(cards)},應為 30')
    dist = collections.Counter(c.get('channel', '?') for c in cards)
    for ch, want in CHANNELS.items():
        if dist.get(ch, 0) != want:
            errors.append(f'頻道「{ch}」有 {dist.get(ch, 0)} 張,應為 {want} 張')
    for extra in set(dist) - set(CHANNELS):
        errors.append(f'出現未定義的頻道「{extra}」')

    for c in cards:
        cid = c.get('id', '?')
        for k in REQUIRED:
            if not c.get(k):
                errors.append(f'{cid} 缺少 {k}')
        if 'ja' in c:
            errors.append(f'{cid} 仍有 ja 欄位(日文已於 2026-08-06 移除)')
        if not c.get('stocks'):
            errors.append(f'{cid} 沒有附個股')
        url = c.get('url', '')
        if url and not url.startswith('http'):
            errors.append(f'{cid} 的 url 不是網址:{url[:40]}')
    if not prompt:
        errors.append('找不到 DISCUSS_PROMPT')

    # ---- 用字 ----
    text = zh_text(cards, prompt)
    used = cjk(text)

    bad = sorted(used & BAD_SET)
    for ch in bad:
        errors.append(f'簡體/日文漢字「{ch}」  {context_of(cards, prompt, ch)}')

    known = read_charfile(BASELINE) | read_charfile(ALLOW) | set(CHANNELS.keys() and ''.join(CHANNELS))
    unknown = sorted(used - known - set(bad))
    for ch in unknown:
        warns.append(f'罕用字「{ch}」  {context_of(cards, prompt, ch)}')

    # ---- 報告 ----
    print(f'卡片 {len(cards)} 張 / {len(dist)} 頻道，中文 {len(text)} 字，用字 {len(used)} 種')
    if errors:
        print(f'\n✗ 硬性錯誤 {len(errors)} 項:')
        for e in errors:
            print('  ', e)
    if warns:
        print(f'\n⚠ 待確認罕用字 {len(warns)} 個(逐一看上下文;是錯字就修,沒問題就加進 {os.path.relpath(ALLOW, ROOT)}):')
        for w in warns:
            print('  ', w)
    if not errors and not warns:
        print('\n✓ 全部通過')

    if errors:
        return 1
    return 2 if warns else 0


def main():
    ap = argparse.ArgumentParser(description="Mo's Feed 晨報上線前檢查")
    ap.add_argument('--rebuild-baseline', action='store_true', help='從 git 歷史重建用字基準')
    ap.add_argument('--min-versions', type=int, default=2, help='收錄門檻(預設 2 個版本)')
    a = ap.parse_args()
    if a.rebuild_baseline:
        rebuild_baseline(a.min_versions)
        return 0
    return check()


if __name__ == '__main__':
    sys.exit(main())
