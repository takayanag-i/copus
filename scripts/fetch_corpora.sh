#!/usr/bin/env bash
# コーパスを取得してテキストにする: Blender マニュアル・GIMP ヘルプ・MDN の日本語版 → <出力フォルダ>/blender.txt・gimp.txt・mdn.txt
# 使い方: bash fetch_corpora.sh <出力フォルダ>   （合わせて約 180MB。数分）
set -euo pipefail
OUT=${1:?出力フォルダを指定する}
mkdir -p "$OUT" && cd "$OUT"
[ -f blender.zip ] || curl -sSL -o blender.zip https://docs.blender.org/manual/ja/latest/blender_manual_html.zip
[ -f gimp.tar.bz2 ] || curl -sSL -o gimp.tar.bz2 https://download.gimp.org/gimp/help/gimp-help-2.6.0-html-ja.tar.bz2
[ -d blender ] || { mkdir blender && unzip -q blender.zip -d blender; }
[ -d gimp ] || { mkdir gimp && tar xjf gimp.tar.bz2 -C gimp; }
if [ ! -d mdn ]; then
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/mdn/translated-content.git mdn
  (cd mdn && git sparse-checkout set files/ja/web/api files/ja/glossary files/ja/web/css files/ja/learn)
fi
python3 - <<'PY'
import os, re, html
def html_text(root, out):
    n = 0
    with open(out, 'w', encoding='utf-8') as o:
        for d, _, fs in os.walk(root):
            for f in fs:
                if not f.endswith('.html'): continue
                t = open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()
                t = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', ' ', t); t = re.sub(r'<[^>]+>', ' ', t)
                t = re.sub(r'[ \t\r]+', ' ', html.unescape(t)); o.write(re.sub(r'\n\s*\n+', '\n', t) + '\n'); n += 1
    return n
print('blender', html_text('blender', 'blender.txt'), 'ページ')
print('gimp', html_text('gimp', 'gimp.txt'), 'ページ')
n = 0
with open('mdn.txt', 'w', encoding='utf-8') as o:
    for d, _, fs in os.walk('mdn/files/ja'):
        for f in fs:
            if f.endswith('.md'): o.write(re.sub(r'\{\{[^}]*\}\}', '', open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()) + '\n'); n += 1
print('mdn', n, 'ページ')
PY
ls -la blender.txt gimp.txt mdn.txt
