"""执行重定位后的完整安装流程，不下载程序、不创建真实用户、不启动服务。"""
import hashlib
import io
import tarfile

from tests.support import StagedCase


class InstallerTests(StagedCase):
    def setUp(self):
        super().setUp()
        archive = self.base / 'node.tar.gz'
        with tarfile.open(archive, 'w:gz') as bundle:
            files = {
                'node/bin/node': '#!/bin/sh\necho MOCK_NODE\n',
                'node/bin/npm': '#!/bin/sh\nprintf "npm %s\\n" "$*" >> "$PW_TEST_LOG"\n',
            }
            for name, source in files.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(source.encode())
                entry.mode = 0o755
                bundle.addfile(entry, io.BytesIO(source.encode()))
        self.env['PW_TEST_ARCHIVE'] = str(archive)
        self.env['PW_TEST_DIGEST'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.python_mock(self.mocks / 'curl', '''
import os, shutil, sys
from pathlib import Path
url = next(x for x in sys.argv if x.startswith('https://'))
target = Path(sys.argv[sys.argv.index('-o') + 1])
with open(os.environ['PW_TEST_LOG'], 'a') as log:
    log.write('curl ' + url + '\\n')
if url.endswith('SHASUMS256.txt'):
    arch = 'x64' if os.environ['PW_TEST_ARCH'] == 'x86_64' else 'arm64'
    platform = 'darwin' if os.environ['PW_TEST_OS'] == 'Darwin' else 'linux'
    filename = f'node-v24.22.1-{platform}-{arch}.tar.gz'
    target.write_text(os.environ['PW_TEST_DIGEST'] + '  ' + filename + '\\n')
else:
    shutil.copyfile(os.environ['PW_TEST_ARCHIVE'], target)
''')

    def install(self, *args):
        return self.shell(self.checkout / 'install.sh', *args)

    def test_linux_installs_template_and_pinned_package(self):
        self.assert_success(self.install('--install-node', '24.22.1', '--install-packages'))
        self.assertTrue((self.root / 'etc/systemd/system/paseo@.service').exists())
        self.assertTrue((self.root / 'usr/local/sbin/paseo-user').exists())
        log = self.log.read_text()
        self.assertIn('node-v24.22.1-linux-x64.tar.gz', log)
        self.assertIn('@getpaseo/cli@0.13.2', log)
        self.assertIn('systemctl daemon-reload', log)

    def test_darwin_supports_both_architectures_without_systemd(self):
        self.env['PW_TEST_OS'] = 'Darwin'
        for arch, artifact in (('arm64', 'arm64'), ('x86_64', 'x64')):
            with self.subTest(arch=arch):
                self.env['PW_TEST_ARCH'] = arch
                self.assert_success(self.install('--install-node', '24.22.1'))
                self.assertIn(f'node-v24.22.1-darwin-{artifact}.tar.gz', self.log.read_text())
                self.assertTrue((self.lib / 'libexec/paseo-daemon').exists())
                self.assertFalse((self.root / 'etc/systemd').exists())
                self.assertNotIn('systemctl', self.log.read_text())

    def test_repeat_install_preserves_configuration_and_previous_node(self):
        self.configure(PW_GROUP='custom-team', PW_PASEO_VERSION='0.13.2')
        before = self.conf.read_text()
        self.assert_success(self.install('--install-node', '24.22.1'))
        (self.node_dir / 'marker').write_text('previous installation')
        self.assert_success(self.install('--install-node', '24.22.1'))
        self.assertEqual(self.conf.read_text(), before)
        self.assertEqual((self.node_dir.with_name('node-shared.old') / 'marker').read_text(),
                         'previous installation')
        self.assertTrue((self.root / 'usr/local/bin/node').is_symlink())

    def test_bad_checksum_does_not_replace_existing_node(self):
        self.configure()
        self.write_executable(self.node_dir / 'bin/node', '#!/bin/sh\necho KEEP\n')
        self.env['PW_TEST_DIGEST'] = '0' * 64
        result = self.install('--install-node', '24.22.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('KEEP', (self.node_dir / 'bin/node').read_text())
        self.assertFalse(self.node_dir.with_name('node-shared.old').exists())

    def test_rejects_incomplete_version_and_unsupported_architecture(self):
        result = self.install('--install-node', '24')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.conf.exists())
        self.env['PW_TEST_ARCH'] = 'unknown-cpu'
        result = self.install('--install-node', '24.22.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_rejects_system_node_prefix(self):
        self.configure(PW_NODE='/usr/bin/node')
        result = self.install('--install-node', '24.22.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('PW_NODE', result.stderr)
        self.assertFalse(self.log.exists())

    def test_missing_node_reports_its_path_in_utf8(self):
        self.configure()
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'找不到 Node：{self.node_dir}/bin/node（', result.stderr)
