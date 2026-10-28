# PocketRig 宣传片（单人版，4 分 05 秒）

[![亮点动图，点击下载完整宣传片](pocketrig-highlights.gif)](pocketrig-promo.mp4)

[下载完整宣传片 MP4](pocketrig-promo.mp4)（1920×1080，H.264 + AAC，纯音乐无字幕，约 17 MB）· [封面](poster.jpg)。GitHub 不会在页面内播放仓库中的 MP4，README 里用自动循环的亮点动图 [`pocketrig-highlights.gif`](pocketrig-highlights.gif) 代替，完整版下载后本地观看。

画面全部由 HTML / SVG 代码重建：账号、主机、地址、项目、任务与指标都是虚构示例，没有使用真实截图或录屏。音乐由 [`source/tools/music.py`](source/tools/music.py) 程序合成，不含采样或第三方版权素材。

## 讲了什么

出发点是**一个人**：自己的手机和 Mac，自己家里一台常开的工作站，重计算交给 GPU 节点。两个亮点：

- **工作站 24 小时在线**：开机自启、客户端断开不影响任务、Windows 上自动保活 WSL。
- **节点上的实验结果，手机上直接看**：节点跑完把小结果拉回工作站，手机打开 Paseo 会话就能看指标和曲线，并接着下指令。

| 时间 | 场景 | 对应 skill |
| --- | --- | --- |
| 0:00 | 人在路上，代码在家里 | — |
| 0:10 | 最常见的两个麻烦 | — |
| 0:26 | 这套工作流怎么跑？ | — |
| 0:33 | 日常设备分工：手机 · MacBook · 常开工作站 · GPU 节点 | [pocketrig-setup](../../skills/pocketrig-setup/SKILL.md) |
| 0:53 | 第一层 · Tailscale 私有网络 | [pocketrig-connect](../../skills/pocketrig-connect/SKILL.md) |
| 1:13 | 第二层 · 工作站上的 Paseo：手机发起，断开照常运行，Mac 接续 | [pocketrig-connect](../../skills/pocketrig-connect/SKILL.md) |
| 1:39 | 亮点 · 工作站 24 小时在线 | [pocketrig-always-on](../../skills/pocketrig-always-on/SKILL.md) |
| 1:55 | 第三层 · 重计算交给节点 | [remote-compute](../../skills/remote-compute/SKILL.md) |
| 2:17 | 亮点 · 手机上直接看实验结果 | [remote-compute](../../skills/remote-compute/SKILL.md) |
| 2:35 | 一天里的一次任务 | — |
| 3:05 | 搭起来只要三步 | [pocketrig-setup](../../skills/pocketrig-setup/SKILL.md) |
| 3:27 | 先说清楚边界 | — |
| 3:43 | 真正值钱的是自己的工作积累 | — |
| 3:55 | 结尾 | [pocketrig-team](../../skills/pocketrig-team/SKILL.md)（扩展给家人或小团队） |

## 重新渲染

工作站只编辑源码；渲染放在已确认的目标机器上执行（Chrome 软件渲染，不用 GPU）。需要 [HyperFrames](https://hyperframes.heygen.com) CLI、GSAP、chrome-headless-shell、ffmpeg，以及带 numpy 与 fontTools 的 Python。

```bash
cd docs/promo/source
export HF_DIR=/path/to/hyperframes-toolchain   # 目录结构见 scripts/env.sh 注释
export PY=/path/to/python                      # 可选，默认 python3
bash scripts/build.sh --music                  # 合成音乐、组装 video/、子集化字体、lint
bash scripts/snap.sh 7,49,111,152,241          # 抽检画面 → review/snap/
bash scripts/render.sh draft                   # 草稿；正式版用 1080p
bash scripts/gif.sh output/<成片>.mp4 pocketrig-highlights.gif   # README 自动播放的亮点动图
```

| 路径 | 作用 |
| --- | --- |
| `source/scenes.json` | 场景顺序与时长，音乐段落随之计算 |
| `source/src/scenes/*.html` | 每个场景一个 HyperFrames 合成（GSAP 时间线） |
| `source/src/shared.css`、`shared.js` | 公共样式与动画工具 |
| `source/tools/build.py` | 组装工程、注入设备示意 SVG、按用到的字子集化字体 |
| `source/tools/music.py` | 合成背景音乐 |
| `source/scripts/gif.sh` | 从成片截取亮点片段，生成 README 用的循环 GIF |

发布版在渲染后用 ffmpeg 转码为网页友好的 H.264（`-crf 24 -preset slow -movflags +faststart`），控制在 GitHub 单文件限制以内。
