#!/bin/zsh
# Build all centring variants (VC/AC/NC) for main, S2T and T2S fonts into the repo root.
cd /Users/seky/Developer/Git/Huiwen-mincho
for m in VC AC NC; do
  for s in "" "-S2T" "-T2S"; do
    PYTHONDONTWRITEBYTECODE=1 python3 -I build_work/cp/make_variants.py HuiwenMincho-AI-v2.1$s.ttf HuiwenMincho-AI-v2.1-$m$s.ttf $m HuiwenMincho-AI-v2.1-$m$s > build_work/cp/log_$m$s.txt 2>&1 &
  done
  wait
done
echo done > build_work/cp/ALL_DONE
