#!/usr/bin/env bash
# 把工作站约定写入本人 ~/.claude/CLAUDE.md 与 ~/.codex/AGENTS.md 的标记区块内。
# 在本人终端执行（paseo-user add 也会以该用户身份调用）；区块外的已有内容保持不变，修改前留备份。
set -euo pipefail
policy=${1:-/usr/local/share/paseo-workstation/workstation-policy.md}
python3 - "$policy" <<'PY'
import sys
from datetime import datetime
from pathlib import Path

start = '<!-- BEGIN WORKSTATION USAGE POLICY -->'
end = '<!-- END WORKSTATION USAGE POLICY -->'
block = f'{start}\n{Path(sys.argv[1]).read_text().strip()}\n{end}\n'

for relative in ('.codex/AGENTS.md', '.claude/CLAUDE.md'):
    path = Path.home() / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text() if path.exists() else ''
    if start in old or end in old:
        if old.count(start) != 1 or old.count(end) != 1:
            raise SystemExit(f'约定标记异常，请手动检查：{path}')
        before, rest = old.split(start, 1)
        _, after = rest.split(end, 1)
        new = before + block.rstrip('\n') + after
    else:
        new = old.rstrip('\n') + ('\n\n' if old else '') + block
    if new != old:
        if path.exists():
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            path.with_name(path.name + '.bak-' + stamp).write_text(old)
        path.write_text(new)
    print(f'已同步：{path}')
PY
