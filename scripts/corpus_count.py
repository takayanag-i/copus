# 句の使われ方をコーパスで数える
# 使い方: CORPUS_DIR=<フォルダ> python3 corpus_count.py 句 [句 ...]
#         CORPUS_DIR=<フォルダ> python3 corpus_count.py --pairs pairs.tsv > counts.tsv
#   pairs.tsv: 1 行 1 組。1 列目は組の名前、2 列目以降は比べる句
#   wiki: 日本語版 Wikipedia の全文検索 API で、その句（引用符で囲んだ完全一致）を含む記事の数。CORPUS_DIR/wiki_cache.json に残す
#   blender・gimp・mdn: CORPUS_DIR の blender.txt・gimp.txt・mdn.txt（fetch_corpora.sh で作る）での出現回数。無いものは数えない
import sys, os, json, time, urllib.request, urllib.parse
CORPUS_DIR = os.environ.get('CORPUS_DIR', '.')
CACHE = os.path.join(CORPUS_DIR, 'wiki_cache.json')
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
texts = {n: open(os.path.join(CORPUS_DIR, n + '.txt'), encoding='utf-8', errors='ignore').read()
         for n in ('blender', 'gimp', 'mdn') if os.path.exists(os.path.join(CORPUS_DIR, n + '.txt'))}

def wiki(q):
    if cache.get(q) is not None: return cache[q]
    url = 'https://ja.wikipedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'list': 'search', 'srsearch': f'"{q}"', 'srinfo': 'totalhits', 'srprop': '', 'srlimit': 1, 'format': 'json'})
    req = urllib.request.Request(url, headers={'User-Agent': 'copus-term-check/1.0 (corpus frequency check)'})
    n = None
    for k in range(4):   # 失敗したら間隔をあけて 4 回まで
        try: n = json.load(urllib.request.urlopen(req, timeout=20))['query']['searchinfo']['totalhits']; break
        except Exception: time.sleep(2 * (k + 1))
    if n is not None:
        cache[q] = n; json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    time.sleep(0.3)
    return n

def count(q):
    return {'wiki': wiki(q), **{k: t.count(q) for k, t in texts.items()}}

if __name__ == '__main__':
    if sys.argv[1:2] == ['--pairs']:
        cols = ['wiki', *texts]
        print('組\t句\t' + '\t'.join(cols))
        for line in open(sys.argv[2], encoding='utf-8'):
            p = [x for x in line.rstrip('\n').split('\t') if x]
            for q in p[1:]:
                c = count(q); print(f'{p[0]}\t{q}\t' + '\t'.join(str(c.get(k)) for k in cols), flush=True)
    else:
        for q in sys.argv[1:]: print(q, json.dumps(count(q), ensure_ascii=False))
