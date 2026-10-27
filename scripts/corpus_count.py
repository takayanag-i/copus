# 句の使われ方をコーパスで数え、密度と加重シェアで比べる
# 使い方: CORPUS_DIR=<フォルダ> python3 corpus_count.py [--context ui|web|prose] [--domain 名前[=重み] ...] [--min 10] [--k 10] 句 [句 ...]
#         CORPUS_DIR=<フォルダ> python3 corpus_count.py --pairs pairs.tsv [同じオプション] > counts.tsv
#   pairs.tsv: 1 行 1 組。1 列目は組の名前、2 列目以降は比べる句
#   wiki: 日本語版 Wikipedia の全文検索 API で、その句（引用符で囲んだ完全一致）を含む記事の数。CORPUS_DIR/wiki_cache.json に残す
#   ほかのコーパス: CORPUS_DIR/corpora.json に登録したもの（build_corpus.py で作る）。その句を含むページの数を数える
#     種類が base のものはいつも数え、domain のものは --domain で名前を指定したときだけ数える
#   密度: wiki は 100 万記事あたりの記事数、ほかは 1,000 ページあたりのページ数
#   加重シェア: 組の中で、コーパスごとに句の割合を取り、重みで平均する。句を 1 つも含まないコーパスは平均に入れない
#     コーパスの重みは、文脈の重みに 件数/(件数+k) を掛けた値。件数はそのコーパスでの組の句の件数の合計
#     文脈の重みは references/weights.csv（文脈,コーパス,重み）。ドメイン固有のコーパスの重みは --domain 名前=重み（省くと 2）
#   根拠: 組の句すべての、全コーパスの記事数とページ数の合計。--min に満たない組は「少ない」と表示する
import os, sys, json, time, argparse, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.environ.get('CORPUS_DIR', '.')
CACHE = os.path.join(CORPUS_DIR, 'wiki_cache.json')
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
UA = {'User-Agent': 'copus-term-check/2.0 (corpus frequency check)'}


def api(params):
    url = 'https://ja.wikipedia.org/w/api.php?' + urllib.parse.urlencode({**params, 'format': 'json'})
    for k in range(4):   # 失敗したら間隔をあけて 4 回まで
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20))
        except Exception:
            time.sleep(2 * (k + 1))
    raise SystemExit(f'Wikipedia API に 4 回続けて失敗した: {params}')


def save():
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


def wiki_articles():
    if '__articles__' not in cache:
        cache['__articles__'] = api({'action': 'query', 'meta': 'siteinfo', 'siprop': 'statistics'})['query']['statistics']['articles']
        save()
    return cache['__articles__']


def wiki(q):
    if cache.get(q) is None:
        cache[q] = api({'action': 'query', 'list': 'search', 'srsearch': f'"{q}"', 'srinfo': 'totalhits',
                        'srprop': '', 'srlimit': 1})['query']['searchinfo']['totalhits']
        save(); time.sleep(0.3)
    return cache[q]


def load_corpora(domains):
    meta_path = os.path.join(CORPUS_DIR, 'corpora.json')
    meta = json.load(open(meta_path, encoding='utf-8')) if os.path.exists(meta_path) else {}
    unknown = [d for d in domains if d not in meta]
    if unknown:
        raise SystemExit(f'corpora.json に無いコーパス: {", ".join(unknown)}。build_corpus.py で作る')
    use = [n for n, m in meta.items() if m['kind'] == 'base' or n in domains]
    pages = {n: open(os.path.join(CORPUS_DIR, n + '.txt'), encoding='utf-8').read().split('\f') for n in use}
    return {n: {'pages': [p for p in pages[n] if p], 'meta': meta[n]} for n in use}


def load_weights(context, domains):
    w = {}
    for line in open(os.path.join(HERE, '..', 'references', 'weights.csv'), encoding='utf-8').read().splitlines()[1:]:
        ctx, corpus, weight = line.split(',')
        if ctx == context:
            w[corpus] = float(weight)
    if not w:
        raise SystemExit(f'weights.csv に文脈 {context} の行が無い')
    return {**w, **domains}


def count(q, corpora):
    total = wiki_articles(); n = wiki(q)
    out = {'wiki': {'件数': n, '密度': round(n / total * 1e6, 2)}}
    for name, c in corpora.items():
        k = sum(1 for p in c['pages'] if q in p)
        out[name] = {'件数': k, '密度': round(k / len(c['pages']) * 1e3, 2)}
    return out


def shares(group, weights, k):
    names = list(next(iter(group.values())).keys())
    n = {c: sum(group[q][c]['件数'] for q in group) for c in names}
    w = {c: weights.get(c, 0) * n[c] / (n[c] + k) for c in names if n[c] > 0}
    wsum = sum(w.values())
    return {q: round(sum(w[c] * group[q][c]['件数'] / n[c] for c in w) / wsum, 3) if wsum else None for q in group}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phrases', nargs='*')
    ap.add_argument('--pairs')
    ap.add_argument('--context', default='prose', choices=['ui', 'web', 'prose'])
    ap.add_argument('--domain', action='append', default=[])
    ap.add_argument('--min', type=int, default=10)
    ap.add_argument('--k', type=float, default=10)
    a = ap.parse_args()
    domains = {}
    for d in a.domain:
        name, _, weight = d.partition('=')
        domains[name] = float(weight) if weight else 2.0
    corpora = load_corpora(domains)
    weights = load_weights(a.context, domains)
    cols = ['wiki', *corpora]
    if a.pairs:
        groups = []
        for line in open(a.pairs, encoding='utf-8'):
            p = [x for x in line.rstrip('\n').split('\t') if x]
            if len(p) >= 3:
                groups.append((p[0], p[1:]))
    else:
        groups = [('-', a.phrases)]
    print('\t'.join(['組', '句', '加重シェア', '根拠', *[f'{c}_{k}' for c in cols for k in ('件数', '密度')]]))
    for name, qs in groups:
        group = {q: count(q, corpora) for q in qs}
        sh = shares(group, weights, a.k)
        evidence = sum(group[q][c]['件数'] for q in qs for c in cols)
        mark = f'{evidence}' if evidence >= a.min else f'{evidence} 少ない'
        for q in qs:
            print('\t'.join([name, q, str(sh[q]), mark, *[str(group[q][c][k]) for c in cols for k in ('件数', '密度')]]), flush=True)


if __name__ == '__main__':
    main()
