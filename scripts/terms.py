# 語の一覧: ファイル一覧の日本語を形態素解析し、名詞の連なり（複合語）を出現回数の順に TSV で出す
# 使い方: python3 terms.py <ファイル一覧> [--min 2]  → 標準出力に「出現回数<TAB>語<TAB>ファイル（最初の 3 つ）<TAB>最初の箇所」
# 要るもの: pip install fugashi unidic-lite
import sys, re, collections, argparse
import fugashi
ap = argparse.ArgumentParser(); ap.add_argument('files'); ap.add_argument('--min', type=int, default=2); a = ap.parse_args()
JA = re.compile(r'[぀-ヿ一-鿿]')
SEG = re.compile(r'[぀-ヿ一-鿿０-ｚー・々ー0-9A-Za-z]+')
tag = fugashi.Tagger()
cnt, files, first = collections.Counter(), collections.defaultdict(list), {}
for f in open(a.files, encoding='utf-8').read().split():
    try: lines = open(f, encoding='utf-8').read().split('\n')
    except (OSError, UnicodeDecodeError): continue
    for ln, line in enumerate(lines, 1):
        if not JA.search(line): continue
        for seg in SEG.findall(line):
            cur = []
            def flush():
                w = ''.join(cur)
                if len(w) >= 2 and JA.search(w):
                    cnt[w] += 1; first.setdefault(w, f'{f}:{ln}')
                    if f not in files[w] and len(files[w]) < 3: files[w].append(f)
                cur.clear()
            for t in tag(seg):
                if t.feature.pos1 in ('名詞', '接尾辞', '接頭辞'): cur.append(t.surface)
                else: flush()
            flush()
for w, c in cnt.most_common():
    if c >= a.min: print(f'{c}\t{w}\t{",".join(files[w])}\t{first[w]}')
