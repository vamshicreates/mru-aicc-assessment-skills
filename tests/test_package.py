import copy
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfReader
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('mru_installer', ROOT / 'install.py')


def fixture(rubric):
    record = dict(
        assessment_id=rubric['assessment_id'], student_name='SYNTHETIC Demo - Étudiant',
        student_number='00123', number_label='Roll number', contact_number='+910000000000',
        submission_key=f"synthetic-validation:{rubric['assessment_id']}",
        source_reference='SYNTHETIC FIXTURE: no real response sheet',
        submission_urls=[], submission_pdf_urls=[], assessed_at='2026-10-27T16:00:00+05:30',
        status='Completed', review_method='Synthetic test; no student media reviewed',
        coverage='Fabricated validation record only', full_visual_review=True,
        full_audio_review=True, answer_key_verified=True, answer_key_reference='Synthetic key',
        overall_feedback='Synthetic feedback for arithmetic and output checks.',
        priorities=['Example improvement.'], missing_items=[], items=[])
    criteria = rubric['criteria'] or [dict(id='q1', label='Example question', max_marks=40),
                                       dict(id='q2', label='Example question', max_marks=60)]
    for criterion in criteria:
        record['items'].append({k: criterion[k] for k in ['id', 'label', 'max_marks']} | dict(
            awarded=criterion['max_marks'] - 1, evidence='00:01-00:03: synthetic evidence only.',
            strengths='Example strength.', gaps='Example gap.',
            rationale='One mark deducted for the synthetic gap.', next_step='Example correction.'))
    return record


class InstallerTests(unittest.TestCase):
    def test_codex_home(self):
        with patch.dict(os.environ, {'CODEX_HOME': str(Path('custom codex'))}):
            self.assertEqual(installer.default_target(), Path('custom codex') / 'skills')

    def test_install_and_idempotent_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'Skills with spaces - café'
            installed = installer.install(target, installer.SKILLS)
            self.assertEqual(len(installed), 3)
            for name in installer.SKILLS:
                self.assertEqual(installer.fingerprints(ROOT / name), installer.fingerprints(target / name))
            self.assertTrue(all(row[1] == 'Already current' for row in installer.install(target, installer.SKILLS)))

    def test_conflict_preflight_and_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'skills'
            destination = target / installer.SKILLS[-1]
            destination.mkdir(parents=True)
            (destination / 'custom.txt').write_text('Keep my customization', encoding='utf-8')
            with self.assertRaises(ValueError):
                installer.install(target, installer.SKILLS)
            self.assertFalse((target / installer.SKILLS[0]).exists())
            installer.install(target, installer.SKILLS, force=True)
            backups = list((target / '.mru-aicc-backups').glob('*/custom.txt'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding='utf-8'), 'Keep my customization')
            self.assertFalse((destination / 'custom.txt').exists())


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.skills = []
        for name in installer.SKILLS:
            path = ROOT / name
            rubric = json.loads((path / 'references/rubric.json').read_text(encoding='utf-8'))
            module = load(name, path / 'scripts/build_report.py')
            self.skills.append((path, rubric, module))

    def test_metadata_rubric_caps_and_source(self):
        for path, rubric, module in self.skills:
            with self.subTest(skill=path.name):
                frontmatter = yaml.safe_load((path / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[1])
                self.assertEqual(frontmatter['name'], path.name)
                metadata = yaml.safe_load((path / 'agents/openai.yaml').read_text(encoding='utf-8'))
                self.assertIn('$' + path.name, metadata['interface']['default_prompt'])
                self.assertEqual(hashlib.sha256((path / 'references/framework.pdf').read_bytes()).hexdigest(), rubric['source_sha256'])
                if rubric['criteria']:
                    self.assertEqual([c['max_marks'] for c in rubric['criteria']], [20, 20, 15, 15, 10, 10, 10])
                    self.assertEqual(sum(c['max_marks'] for c in rubric['criteria']), 100)

    def test_full_and_pending_reports_preserve_identifiers(self):
        with tempfile.TemporaryDirectory() as temporary:
            for path, rubric, module in self.skills:
                with self.subTest(skill=path.name):
                    data = fixture(rubric)
                    result = module.render(data, rubric, Path(temporary))
                    expected = 100 - len(data['items'])
                    self.assertEqual(result['final_score'], str(expected))
                    extracted = ' '.join(page.extract_text() for page in PdfReader(result['pdf']).pages)
                    self.assertIn('00123', extracted)
                    self.assertIn('Final score:', extracted)
                    with open(result['csv'], encoding='utf-8-sig', newline='') as handle:
                        row = next(csv.DictReader(handle))
                    self.assertEqual(row['Roll number'], '00123')
                    self.assertEqual(row['Contact number'], '+910000000000')
                    # Repeated theory question labels must retain separate score columns.
                    for item in data['items']:
                        self.assertIn(item['id'] + ' — ' + item['label'], row)
                    data['status'] = 'Provisional'
                    data['items'][0]['awarded'] = None
                    result = module.render(data, rubric, Path(temporary))
                    self.assertIsNone(result['final_score'])
                    with open(result['csv'], encoding='utf-8-sig', newline='') as handle:
                        self.assertEqual(next(csv.DictReader(handle))['Total /100'], '')

    def test_invalid_or_unsupported_final_marks_are_rejected(self):
        for path, rubric, module in self.skills:
            original = fixture(rubric)
            changes = [
                lambda d: d['items'][0].update(awarded=101),
                lambda d: d['items'][0].update(awarded=True),
                lambda d: d['items'][0].update(awarded=float('nan')),
                lambda d: d['items'][0].update(awarded=None),
                lambda d: d['items'][0].update(evidence=''),
                lambda d: d.update(student_number=123),
            ]
            changes.append((lambda d: d.update(answer_key_verified=False)) if rubric['assessment_id'] == 1
                           else (lambda d: d.update(full_audio_review=False)))
            for change in changes:
                data = copy.deepcopy(original)
                change(data)
                with self.subTest(skill=path.name, changed=repr(data['items'][0])):
                    with self.assertRaises(ValueError):
                        module.validate(data, rubric)

    def test_windows_bom_and_ascii_console_via_actual_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'Reports with spaces - café'
            folder.mkdir()
            path, rubric, module = self.skills[1]
            source = folder / 'student.json'
            source.write_text(json.dumps(fixture(rubric), ensure_ascii=False), encoding='utf-8-sig')
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'ascii'
            result = subprocess.run([sys.executable, str(path / 'scripts/build_report.py'), str(source),
                                     '--output-dir', str(folder)], env=env, capture_output=True, check=True)
            output = json.loads(result.stdout.decode('ascii'))
            self.assertEqual(output['final_score'], '93')
            self.assertTrue(Path(output['pdf']).is_file())


if __name__ == '__main__':
    unittest.main()
