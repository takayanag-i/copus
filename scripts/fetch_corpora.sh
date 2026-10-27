#!/usr/bin/env bash
# 基本のコーパスを取得して作る: Blender マニュアル・MDN・OpenTelemetry の日本語版 → <出力フォルダ>/blender.txt・mdn.txt・otel.txt と corpora.json
# 使い方: bash fetch_corpora.sh <出力フォルダ>   （ダウンロードは約 400MB。数分）
# ドメイン固有のコーパスは、文書を取得してから build_corpus.py に --domain を付けて作る（README の「ドメイン固有のコーパス」）
set -euo pipefail
OUT=${1:?出力フォルダを指定する}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT" && cd "$OUT"
[ -f blender.zip ] || curl -sSL -o blender.zip https://docs.blender.org/manual/ja/latest/blender_manual_html.zip
[ -d blender ] || { mkdir blender && unzip -q blender.zip -d blender; }
if [ ! -d mdn ]; then
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/mdn/translated-content.git mdn
  (cd mdn && git sparse-checkout set files/ja/web/api files/ja/glossary files/ja/web/css files/ja/learn)
fi
if [ ! -d otel ]; then
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/open-telemetry/opentelemetry.io.git otel
  (cd otel && git sparse-checkout set content/ja)
fi
python3 -I "$HERE/build_corpus.py" blender blender . --ext .html --exclude '/(genindex|search|404|versions|copyright)\.html$'
python3 -I "$HERE/build_corpus.py" mdn mdn/files/ja . --ext .md
python3 -I "$HERE/build_corpus.py" otel otel/content/ja . --ext .md
