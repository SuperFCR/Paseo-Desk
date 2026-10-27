# 手机发起，Mac 接续

30 秒无声流程短片，5 个场景，每场 6 秒。手机和 Mac 都是客户端，接入同一工作站上的本人 Paseo 实例；本片不演示 macOS 工作站部署。

[播放 / 下载 MP4](paseo-phone-mac.mp4)（720p，约 255 KiB）。画面与分镜由 GPT-6 Astra 制作，在计算节点渲染。

[![脱敏短片封面](poster.png)](paseo-phone-mac.mp4)

直接用浏览器打开 [`index.html`](index.html) 可离线播放。支持暂停、前后场景、时间拖动，以及空格、方向键、Home / End。页面不加载外部字体、脚本、图片，也不采集信息；字形使用本机中文字体。

| 时间 | 画面 |
| --- | --- |
| 00–06 秒 | 手机通过 Tailscale，发起少量模拟数据的报告任务 |
| 06–12 秒 | Mac 进入相同 Host、成员身份、工作区与会话，继续修改 |
| 12–18 秒 | 查看虚构 Markdown 报告与 SVG 图表 |
| 18–24 秒 | 工作站负责轻量开发，SSH 节点负责数据与模型计算 |
| 24–30 秒 | 每人独立身份与账号，展示模拟用量与隐私边界 |

## 在目标机器生成 MP4

工作站只编辑与检查源码。把本目录的公开源码同步到已确认的目标机器，再在那里运行。需要 Python 3.9+、Chrome / Chromium（含 headless shell）、带 libx264 的 ffmpeg，以及中文字体（如 Noto Sans CJK SC）。脚本本身只使用 Python 标准库，不下载任何依赖。

```bash
# 在目标机器上；路径替换为该机器已安装的程序及获授权目录。
python3 render.py \
  --browser /path/to/chrome-headless-shell \
  --ffmpeg /path/to/ffmpeg \
  --output /path/to/authorized/paseo-video-output \
  --keep-work
```

输出为 `paseo-phone-mac.mp4`：1280×720、H.264、24 fps、30 秒、无音轨、不使用 GPU，ffmpeg 编码线程不超过 2。脚本去除输入元数据和章节；容器仍有格式必需的技术字段。若成片超过 10 MiB，脚本报错并保留工作目录供检查。输出已存在时会拒绝覆盖，换一个输出目录即可。

每场景 PNG、日志、临时编码文件及 Chrome 的 HOME、profile、缓存、临时目录都位于输出目录的 `.render-work/run-…/`。默认成功后清理；`--keep-work` 保留它们，便于检查字体与构图。失败时保留现场。仅在隔离目标环境确有需要时加 `--no-sandbox`。目标机器已有库依赖环境时，先按该机器的说明加载环境。

`index.html?scene=2&export=1` 可固定导出第 2 场，编号范围 1–5；此模式为 1280×720，不显示播放控件，没有动画或自动换场。正式导出前应检查五张 PNG：中文能正常显示、没有裁切，且示意标识持续可见。可用 `ffprobe` 核验最终成片：

```bash
ffprobe -v error -show_entries \
  stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size \
  -of json /path/to/authorized/paseo-video-output/paseo-phone-mac.mp4
```

## 内容边界

所有界面均由 HTML/CSS 原生重建，并持续标记“流程示意 / 虚构数据”和“非真实录屏”。未复制、上传或嵌入真实截图。人物、主机、邮箱、路径、用量与结果均为虚构占位，不含密码、IP、密钥或登录凭据。片中报告和文件只是分镜内容，不代表本目录提供了对应运行程序，也不代表端到端部署验收通过。

用量百分比不能换算成订阅实际美元支出；个人账号按各自授权使用。CLI 会话控制不代表桌面 CUA。真实数据、模型及重计算留在计算节点，按需取回小型结果。手机断线或停止代理也不等于远程作业已停止。实际连接步骤以[成员教程](../user-guide.md)为准。
