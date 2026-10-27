import json
import os
import plistlib
import re
import runpy
from types import SimpleNamespace
from unittest import TestCase, mock
from urllib.parse import unquote

from tests.support import REPO, StagedCase


class WrapperTests(StagedCase):
    def setUp(self):
        super().setUp()
        self.configure(PW_GROUP="''")
        (self.lib / 'libexec').mkdir(parents=True)
        (self.lib / 'libexec/env.sh').write_text((self.checkout / 'libexec/env.sh').read_text())
        self.hooks = self.conf.parent / 'pre-launch.d'
        self.hooks.mkdir()
        self.write_executable(self.node_dir / 'bin/node', '#!/bin/sh\nprintf "MOCK_NODE:%s\\n" "$*"\n')
        self.cli = self.root / 'usr/local/lib/codex-shared/node_modules/.bin/codex'
        self.write_executable(self.cli, '#!/usr/bin/env node\n')

    def test_noninteractive_provider_finds_configured_node(self):
        result = self.shell(self.checkout / 'bin/codex', 'one argument', '--json')
        self.assert_success(result)
        self.assertIn('MOCK_NODE:', result.stdout)
        self.assertIn('one argument --json', result.stdout)

    def test_successful_hook_keeps_stdout_clean_and_preserves_arguments(self):
        self.write_executable(self.hooks / '10-check', '#!/bin/sh\necho CHECKED\n')
        self.python_mock(self.cli, 'import json, sys\nprint(json.dumps(sys.argv[1:]))\n')
        args = ['two words', '', '$(not-a-command)', '*']
        result = self.shell(self.checkout / 'bin/codex', *args)
        self.assert_success(result)
        self.assertEqual(json.loads(result.stdout), args)
        self.assertIn('CHECKED', result.stderr)

    def test_failed_hook_prevents_provider_execution(self):
        self.write_executable(self.hooks / '10-deny', '#!/bin/sh\necho DENIED\nexit 1\n')
        result = self.shell(self.checkout / 'bin/codex', '--version')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('DENIED', result.stderr)
        self.assertIn(f'启动前检查失败：{self.hooks}/10-deny，已拒绝启动 codex。',
                      result.stderr)

    def test_group_denial_reports_provider_name_in_utf8(self):
        self.configure(PW_GROUP='demo-team')
        result = self.shell(self.checkout / 'bin/codex', '--version')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('请以 demo-team 组成员身份运行 codex（不要用 sudo）。', result.stderr)


class UserConfigTests(StagedCase):
    def setUp(self):
        super().setUp()
        self.namespace = runpy.run_path(str(REPO / 'linux/sbin/paseo-user'))
        self.module_globals = self.namespace['write_config'].__globals__
        self.owner = self.namespace['Owner'](SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid()))
        self.paseo = self.base / 'user/.paseo'
        self.owner.directory(self.paseo)

    def test_merge_preserves_provider_options_and_user_preferences(self):
        path = self.paseo / 'config.json'
        path.write_text(json.dumps({
            'version': 1, 'custom': {'keep': True},
            'agents': {'providers': {'codex': {'env': {'EXAMPLE': 'keep'}},
                                     'other': {'command': ['another-cli']}}},
            'features': {'dictation': {'enabled': True}},
        }))
        self.namespace['write_config'](self.owner, self.paseo, '127.0.0.1:6768', 'HASH')
        config = json.loads(path.read_text())
        self.assertEqual(config['daemon']['listen'], '127.0.0.1:6768')
        self.assertEqual(config['daemon']['auth']['password'], 'HASH')
        self.assertFalse(config['daemon']['relay']['enabled'])
        self.assertEqual(config['agents']['providers']['codex']['env'], {'EXAMPLE': 'keep'})
        self.assertEqual(config['agents']['providers']['other']['command'], ['another-cli'])
        self.assertTrue(config['features']['dictation']['enabled'])
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_new_user_enables_web_and_disables_local_voice(self):
        self.namespace['write_config'](self.owner, self.paseo, '127.0.0.1:6767', 'HASH')
        config = json.loads((self.paseo / 'config.json').read_text())
        self.assertTrue(config['features']['webUi']['enabled'])
        self.assertFalse(config['features']['dictation']['enabled'])
        self.assertFalse(config['features']['voiceMode']['enabled'])
        self.assertEqual(self.paseo.stat().st_mode & 0o777, 0o700)

    def test_port_collision_rejected_before_account_mutation(self):
        with mock.patch.dict(self.module_globals, assigned_ports=lambda: {'bob': 6768}):
            with mock.patch('subprocess.run') as command:
                with self.assertRaises(SystemExit):
                    self.namespace['cmd_add']({}, SimpleNamespace(user='alice', port=6768))
                command.assert_not_called()


class PolicyTests(StagedCase):
    def test_policy_sync_is_private_idempotent_and_preserves_notes(self):
        user_home = self.base / 'policy-user'
        user_home.mkdir()
        env = dict(self.env, HOME=str(user_home))
        script = REPO / 'linux/share/sync-agent-policy.sh'
        policy = REPO / 'linux/share/workstation-policy.md'
        self.assert_success(self.shell(script, str(policy), env=env))
        path = user_home / '.claude/CLAUDE.md'
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
        path.write_text('PERSONAL NOTES\n\n' + path.read_text())
        before = path.read_text()
        self.assert_success(self.shell(script, str(policy), env=env))
        self.assertEqual(path.read_text(), before)
        self.assertEqual(path.read_text().count('<!-- BEGIN WORKSTATION USAGE POLICY -->'), 1)


class TemplateTests(TestCase):
    def test_launchd_template_runs_foreground_as_member_with_private_umask(self):
        source = (REPO / 'macos/sh.paseo.workstation.USER.plist.template').read_text()
        config = plistlib.loads(source.replace('__USER__', 'alice').replace(
            '__LISTEN__', '127.0.0.1:6767').encode())
        self.assertEqual(config['UserName'], 'alice')
        self.assertEqual(config['Umask'], 0o077)
        self.assertTrue(config['KeepAlive'])
        self.assertEqual(config['EnvironmentVariables']['HOME'], '/Users/alice')
        self.assertEqual(config['StandardErrorPath'], '/Users/alice/.paseo/launchd.log')
        entry = REPO / 'linux/libexec/paseo-daemon'
        self.assertIn('daemon run', entry.read_text())
        self.assertEqual(config['ProgramArguments'],
                         ['/usr/local/lib/paseo-workstation/libexec/paseo-daemon'])

    def test_documentation_local_links_exist(self):
        for path in REPO.rglob('*.md'):
            if '.git' in path.parts:
                continue
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if re.match(r'\w+:', target) or target.startswith('#'):
                    continue
                target = unquote(target.split('#', 1)[0])
                with self.subTest(document=path.relative_to(REPO), target=target):
                    self.assertTrue((path.parent / target).exists())
