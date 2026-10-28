#!/usr/bin/env python3
"""把 src/ 组装成 hyperframes 工程 video/。

模板占位：
  /*SHARED_CSS*/ /*SHARED_JS*/   公共样式与动画工具
  {{dur}}                        本场景时长（秒）
  {{dev:名称:宽度}}               设备示意 SVG（phone / laptop / desk / gpu）
在目标机器运行；字体子集化需要 fontTools（--no-fonts 跳过，用于只检查结构）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "src", ROOT / "video"
HF = Path(os.environ.get("HF_DIR", "/opt/hyperframes"))  # 只读复用：GSAP 与字体源文件，由 scripts/env.sh 传入

DEV = {
    "phone": (120, 230, """
<defs><linearGradient id="gPh" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#45454e"/><stop offset="1" stop-color="#141418"/></linearGradient>
<linearGradient id="gPs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c2535"/><stop offset="1" stop-color="#0c1017"/></linearGradient></defs>
<rect x="2" y="2" width="116" height="226" rx="22" fill="url(#gPh)" stroke="#5c5c66" stroke-width="2"/>
<rect x="8" y="8" width="104" height="214" rx="17" fill="url(#gPs)"/>
<rect x="44" y="15" width="32" height="9" rx="4.5" fill="#000"/>
<rect x="18" y="44" width="62" height="16" rx="6" fill="#2b3a52"/>
<rect x="40" y="68" width="62" height="24" rx="8" fill="#f2b64c" opacity=".88"/>
<rect x="18" y="102" width="78" height="9" rx="4" fill="#2c3646"/>
<rect x="18" y="117" width="60" height="9" rx="4" fill="#2c3646"/>
<rect x="18" y="132" width="70" height="9" rx="4" fill="#2c3646"/>
<rect x="16" y="196" width="88" height="15" rx="7.5" fill="#222934"/>"""),
    "laptop": (260, 172, """
<defs><linearGradient id="gLw" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2b4f9c"/><stop offset=".55" stop-color="#4a3384"/><stop offset="1" stop-color="#101632"/></linearGradient>
<linearGradient id="gLb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e3e5ea"/><stop offset="1" stop-color="#8d9098"/></linearGradient></defs>
<rect x="30" y="4" width="200" height="138" rx="9" fill="#18181d" stroke="#55555f" stroke-width="2"/>
<rect x="38" y="12" width="184" height="122" rx="3" fill="url(#gLw)"/>
<rect x="56" y="30" width="112" height="78" rx="5" fill="#0f1118" opacity=".92"/>
<rect x="64" y="40" width="54" height="6" rx="3" fill="#f2b64c"/>
<rect x="64" y="54" width="90" height="5" rx="2.5" fill="#3b4255"/>
<rect x="64" y="65" width="76" height="5" rx="2.5" fill="#3b4255"/>
<rect x="64" y="76" width="84" height="5" rx="2.5" fill="#3b4255"/>
<rect x="64" y="91" width="40" height="7" rx="3.5" fill="#6fd39b" opacity=".85"/>
<path d="M6 144 H254 L242 164 Q240 168 234 168 H26 Q20 168 18 164 Z" fill="url(#gLb)"/>
<rect x="110" y="144" width="40" height="5" rx="2.5" fill="#6d7078"/>"""),
    "desk": (190, 214, """
<defs><linearGradient id="gDk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a3a43"/><stop offset="1" stop-color="#121216"/></linearGradient>
<radialGradient id="gDl"><stop offset="0" stop-color="#ffd58a"/><stop offset="1" stop-color="#f2b64c" stop-opacity="0"/></radialGradient></defs>
<rect x="36" y="6" width="118" height="196" rx="12" fill="url(#gDk)" stroke="#5a5a64" stroke-width="2"/>
<rect x="48" y="20" width="94" height="34" rx="6" fill="#0d0d11" stroke="#2c2c34"/>
<circle cx="125" cy="37" r="14" fill="url(#gDl)"/><circle cx="125" cy="37" r="4.5" fill="#ffd58a"/>
<rect x="56" y="33" width="44" height="7" rx="3.5" fill="#2e2e37"/>
<g fill="#26262e"><rect x="52" y="72" width="86" height="5" rx="2.5"/><rect x="52" y="84" width="86" height="5" rx="2.5"/><rect x="52" y="96" width="86" height="5" rx="2.5"/>
<rect x="52" y="108" width="86" height="5" rx="2.5"/><rect x="52" y="120" width="86" height="5" rx="2.5"/><rect x="52" y="132" width="86" height="5" rx="2.5"/>
<rect x="52" y="144" width="86" height="5" rx="2.5"/><rect x="52" y="156" width="86" height="5" rx="2.5"/></g>
<rect x="56" y="176" width="78" height="12" rx="6" fill="#1a1a20" stroke="#34343d"/>
<rect x="44" y="202" width="20" height="8" rx="2" fill="#222228"/><rect x="126" y="202" width="20" height="8" rx="2" fill="#222228"/>"""),
    "gpu": (236, 190, """
<defs><linearGradient id="gGu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b3b45"/><stop offset="1" stop-color="#18181d"/></linearGradient></defs>
<g id="gGr"><rect x="6" y="8" width="224" height="52" rx="7" fill="url(#gGu)" stroke="#5a5a66" stroke-width="2"/>
<g fill="#121216"><rect x="20" y="20" width="110" height="5" rx="2"/><rect x="20" y="30" width="110" height="5" rx="2"/><rect x="20" y="40" width="110" height="5" rx="2"/></g>
<rect x="146" y="22" width="44" height="22" rx="4" fill="#101014" stroke="#2e2e36"/>
<circle cx="204" cy="27" r="3.6" fill="#6fd39b"/><circle cx="216" cy="27" r="3.6" fill="#a597ff"/><circle cx="204" cy="40" r="3.6" fill="#6fd39b" opacity=".6"/></g>
<use href="#gGr" y="60"/><use href="#gGr" y="120"/>"""),
}


def dev_svg(name: str, width: str) -> str:
    w, h, body = DEV[name]
    width = float(width)
    return (f'<svg viewBox="0 0 {w} {h}" width="{width:g}" height="{width * h / w:.1f}" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


def font_faces() -> str:
    return (
        '@font-face { font-family: "NotoSansSC"; src: url("assets/fonts/NotoSansSC.woff2") format("woff2"); '
        "font-weight: 100 900; font-display: block; }\n"
        '@font-face { font-family: "JBMono"; src: url("assets/fonts/JBMono.woff2") format("woff2"); '
        "font-weight: 100 800; font-display: block; }\n"
    )


def visible_text(html: str) -> str:
    html = re.sub(r"<(style)[\s\S]*?</\1>", " ", html)
    return re.sub(r"<[^>]+>", " ", html)  # 保留脚本里的字符串，宁多勿少


def subset_fonts(text: str) -> None:
    dst = OUT / "assets" / "fonts"
    dst.mkdir(parents=True, exist_ok=True)
    base = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
               "·×+−-=—/\\.:;,!?~@#$%&*()[]{}<>'\"_|^`？！，。：；、“”‘’（）《》→←↑↓✓✕…")
    chars = "".join(sorted((set(text) | base) - set(" \t\r\n")))
    tmp = OUT / ".chars.txt"
    tmp.write_text(chars, encoding="utf-8")
    for src, name in (("NotoSansSC[wght].ttf", "NotoSansSC"), ("JetBrainsMono[wght].ttf", "JBMono")):
        subprocess.run([sys.executable, "-m", "fontTools.subset", str(HF / "models" / "fonts" / src),
                        f"--text-file={tmp}", "--flavor=woff2", "--layout-features=*",
                        f"--output-file={dst / (name + '.woff2')}"], check=True)
    tmp.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fonts", action="store_true")
    args = ap.parse_args()

    scenes = json.loads((ROOT / "scenes.json").read_text(encoding="utf-8"))
    css = font_faces() + (SRC / "shared.css").read_text(encoding="utf-8")
    js = (SRC / "shared.js").read_text(encoding="utf-8")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "compositions").mkdir(parents=True)

    hosts, texts, t = [], [], 0.0
    for k, sc in enumerate(scenes):
        sid, dur = sc["id"], float(sc["dur"])
        html = (SRC / "scenes" / f"{sid}.html").read_text(encoding="utf-8")
        html = re.sub(r"\{\{dev:(\w+):([\d.]+)\}\}", lambda m: dev_svg(m[1], m[2]), html)
        html = html.replace("/*SHARED_CSS*/", css).replace("/*SHARED_JS*/", js).replace("{{dur}}", f"{dur:g}")
        left = re.findall(r"\{\{[^}]*\}\}", html)
        if left:
            raise SystemExit(f"{sid}: 未替换的占位 {left}")
        (OUT / "compositions" / f"{sid}.html").write_text(html, encoding="utf-8")
        texts.append(visible_text(html))
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{t:.3f}" data-duration="{dur:.3f}" data-track-index="{k + 1}" '
                     f'data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{k + 1}"></div>')
        t += dur

    audio = ""
    music = ROOT / "audio" / "music.wav"
    if music.exists():
        (OUT / "assets" / "audio").mkdir(parents=True, exist_ok=True)
        shutil.copy2(music, OUT / "assets" / "audio" / "music.wav")
        audio = (f'<audio id="music" class="clip" data-start="0" data-duration="{t:.3f}" data-track-index="30" '
                 'data-volume="1" src="assets/audio/music.wav"></audio>')
    index = (SRC / "index.html").read_text(encoding="utf-8")
    index = (index.replace("/*FONT_FACES*/", font_faces()).replace("{{TOTAL}}", f"{t:.3f}")
             .replace("{{SCENE_HOSTS}}", "\n      ".join(hosts)).replace("{{AUDIO}}", audio))
    (OUT / "index.html").write_text(index, encoding="utf-8")

    vend = OUT / "assets" / "vendor"
    vend.mkdir(parents=True)
    shutil.copy2(HF / "node_modules" / "gsap" / "dist" / "gsap.min.js", vend / "gsap.min.js")
    for f in ("hyperframes.json", "meta.json"):
        shutil.copy2(SRC / f, OUT / f)
    if not args.no_fonts:
        subset_fonts("".join(texts))
    print(f"总长 {t:.1f}s，{len(scenes)} 个场景，音乐 {'已接入' if audio else '缺失'}")


if __name__ == "__main__":
    main()
