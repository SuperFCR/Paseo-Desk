"""在临时目录重定位安装路径；所有网络、root 身份与 systemctl 均为模拟。"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]


class StagedCase(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='paseo-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'root'
        self.checkout = self.base / 'checkout'
        shutil.copytree(REPO / 'linux', self.checkout)
        # 只改测试副本的安装常量，不修改仓库源码或访问真实部署目录。
        for path in self.checkout.rglob('*'):
            if path.is_file():
                text = path.read_text()
                for prefix in ('/usr/local', '/etc/paseo-workstation', '/etc/systemd'):
                    text = text.replace(prefix, str(self.root) + prefix)
                path.write_text(text)
        self.mocks = self.base / 'mock-bin'
        self.mocks.mkdir()
        self.log = self.base / 'commands.log'
        self.env = dict(os.environ, PATH=f'{self.mocks}{os.pathsep}{os.defpath}',
                        PW_TEST_LOG=str(self.log), PW_TEST_OS='Linux', PW_TEST_ARCH='x86_64')
        self.write_executable(self.mocks / 'uname',
                              '#!/bin/sh\ncase "$1" in -s) echo "$PW_TEST_OS";; -m) echo "$PW_TEST_ARCH";; esac\n')
        self.write_executable(self.mocks / 'id', '#!/bin/sh\necho 0\n')
        self.write_executable(self.mocks / 'systemctl',
                              '#!/bin/sh\nprintf "systemctl %s\\n" "$*" >> "$PW_TEST_LOG"\n')
        self.conf = self.root / 'etc/paseo-workstation/workstation.conf'
        self.lib = self.root / 'usr/local/lib/paseo-workstation'
        self.node_dir = self.root / 'usr/local/lib/node-shared'

    @staticmethod
    def write_executable(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)

    def configure(self, **values):
        self.conf.parent.mkdir(parents=True, exist_ok=True)
        text = (self.checkout / 'workstation.conf.example').read_text()
        for key, value in values.items():
            lines = text.splitlines()
            text = '\n'.join(f'{key}={value}' if line.startswith(key + '=') else line
                             for line in lines) + '\n'
        self.conf.write_text(text)

    def shell(self, script, *args, env=None):
        return subprocess.run(['bash', str(script), *args], env=env or self.env,
                              capture_output=True, text=True, timeout=20)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def python_mock(self, path, source):
        self.write_executable(path, f'#!{sys.executable}\n' + source)
