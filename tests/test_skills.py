"""Skills 与插件清单的结构检查：不调用任何 Agent，也不写入本人 skills 目录。"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / 'skills'


def frontmatter(path):
    text = path.read_text(encoding='utf-8')
    match = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not match:
        return None
    return dict(re.findall(r'^(\w[\w-]*):\s*(.+)$', match.group(1), re.M))


class SkillTests(TestCase):
    def skill_dirs(self):
        return sorted(p.parent for p in SKILLS.glob('*/SKILL.md'))

    def test_every_skill_has_matching_name_and_trigger_description(self):
        dirs = self.skill_dirs()
        self.assertGreaterEqual(len(dirs), 6)
        for d in dirs:
            with self.subTest(skill=d.name):
                meta = frontmatter(d / 'SKILL.md')
                self.assertIsNotNone(meta, 'SKILL.md 缺少 frontmatter')
                self.assertEqual(meta.get('name'), d.name)
                self.assertRegex(d.name, r'^[a-z0-9]+(-[a-z0-9]+)*$')
                self.assertGreater(len(meta.get('description', '')), 40)
                self.assertLessEqual(len(meta['description']), 1024)

    def test_skills_index_lists_every_skill(self):
        index = (SKILLS / 'README.md').read_text(encoding='utf-8')
        for d in self.skill_dirs():
            with self.subTest(skill=d.name):
                self.assertIn(f'({d.name}/SKILL.md)', index)

    def test_skills_contain_no_secrets_or_real_addresses(self):
        pattern = re.compile(r'PASEO_PASSWORD=\S|BEGIN [A-Z ]*PRIVATE KEY|tskey-|sk-ant-|\b100\.(?!x\.y\.z)\d+\.\d+\.\d+')
        for path in SKILLS.rglob('*'):
            if path.is_file():
                with self.subTest(file=path.relative_to(REPO)):
                    self.assertIsNone(pattern.search(path.read_text(encoding='utf-8')))

    def test_plugin_and_marketplace_manifests(self):
        plugin = json.loads((REPO / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        market = json.loads((REPO / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))
        self.assertEqual(plugin['name'], 'paseo-desk')
        for rel in plugin['skills']:
            self.assertTrue((REPO / rel).is_dir())
        entry = next(p for p in market['plugins'] if p['name'] == plugin['name'])
        self.assertEqual(entry['source'], './')
        self.assertEqual(entry['version'], plugin['version'])

    def test_installer_copies_skills_and_backs_up_existing(self):
        with tempfile.TemporaryDirectory(prefix='paseo-skills-') as tmp:
            target = Path(tmp) / 'skills'
            (target / 'paseo-desk-setup').mkdir(parents=True)
            (target / 'paseo-desk-setup' / 'SKILL.md').write_text('old', encoding='utf-8')
            env = dict(os.environ, HOME=tmp, LC_ALL='C.UTF-8')
            for _ in range(2):
                subprocess.run([str(SKILLS / 'install.sh'), '--target', str(target)],
                               check=True, env=env, capture_output=True)
            installed = sorted(p.name for p in target.iterdir() if '.bak-' not in p.name)
            self.assertEqual(installed, [d.name for d in self.skill_dirs()])
            self.assertTrue(any(p.name.startswith('paseo-desk-setup.bak-') for p in target.iterdir()))
            self.assertIn('name: paseo-desk-setup',
                          (target / 'paseo-desk-setup' / 'SKILL.md').read_text(encoding='utf-8'))
