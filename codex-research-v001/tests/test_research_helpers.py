from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jsonschema
from fixture_factory import create_fixture, digest, put_json

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / 'scripts' / 'research'
SCHEMAS = PACKAGE / 'schemas' / 'research'


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='research-v001-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root = create_fixture(Path(self.temp.name) / 'root')

    def load(self, path):
        return json.loads((self.root / path).read_text(encoding='utf-8'))

    def save(self, path, data):
        put_json(self.root / path, data)

    def rebind_receipt(self):
        receipt = self.load('receipt.json')
        receipt['contract_sha256'] = digest(self.root / 'contract.json')
        self.save('receipt.json', receipt)

    def invoke(self, tool, *arguments, code=0, raw=False):
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS/(tool+'.py')), '--root', str(self.root),
                                 '--policy', 'policy.json', *arguments], capture_output=True, check=False)
        self.assertEqual(result.returncode, code, result.stdout.decode('utf-8') + result.stderr.decode('utf-8'))
        self.assertEqual(result.stderr, b'')
        if raw:
            return result.stdout
        doc = json.loads(result.stdout)
        jsonschema.Draft202012Validator(json.loads((SCHEMAS/'helper_report.schema.json').read_text())).validate(doc)
        return doc

    def audit(self, tool='audit_result', *extra, code=0, raw=False):
        return self.invoke(tool, '--authority', 'authority.json', '--target', 'source', '--lineage', 'lineage.json',
                           '--contract', 'contract.json', '--receipt', 'receipt.json', *extra, code=code, raw=raw)

    def preflight(self, *extra, code=0):
        contract = self.load('contract.json')
        contract['outputs'][0]['path'] = 'future-result.json'
        self.save('contract.json', contract)
        return self.invoke('experiment_preflight', '--authority', 'authority.json', '--target', 'source',
                           '--lineage', 'lineage.json', '--contract', 'contract.json', *extra, code=code)

    def tree(self):
        return {str(path.relative_to(self.root)): digest(path) for path in self.root.rglob('*') if path.is_file()}

    def test_01_pipeline_is_deterministic_and_non_destructive(self):
        before = self.tree()
        authority = self.invoke('verify_authority', '--manifest', 'authority.json', '--target', 'source', '--dry-run')
        self.assertEqual(authority['data']['authority_state'], 'AUTHORITY_EXACT')
        self.invoke('verify_hashes', '--manifest', 'hashes.json', '--dry-run')
        self.invoke('verify_lineage', '--manifest', 'lineage.json', '--dry-run')
        audit = self.audit('audit_result', '--dry-run')
        jsonschema.Draft202012Validator(json.loads((SCHEMAS/'result_audit.schema.json').read_text())).validate(audit)
        self.assertEqual(audit['data']['layers']['scientific_status'], 'NOT_ASSESSED')
        self.assertEqual(audit['data']['layers']['semantic_status'], 'NOT_ASSESSED')
        first = self.audit('build_handoff', '--dry-run', raw=True)
        self.assertEqual(first, self.audit('build_handoff', '--dry-run', raw=True))
        self.assertEqual(before, self.tree())

    def test_02_authority_states(self):
        original = self.load('authority.json')
        cases = [('AUTHORITY_AMBIGUOUS', [original['authorities'][0]]*2),
                 ('AUTHORITY_SUPERSEDED', [{**original['authorities'][0], 'state':'retired'}]),
                 ('AUTHORITY_NOT_FOUND', [{**original['authorities'][0], 'id':'different'}]),
                 ('AUTHORITY_NOT_VERIFIED', [{**original['authorities'][0], 'state':'candidate'}])]
        for expected, entries in cases:
            with self.subTest(expected=expected):
                self.save('authority.json', {'schema_version':'1','authorities':entries})
                report = self.invoke('verify_authority', '--manifest', 'authority.json', '--target', 'source', code=1)
                self.assertEqual(report['data']['authority_state'], expected)

    def test_03_remote_and_missing_authority_are_unverified(self):
        doc = self.load('authority.json')
        entry = doc['authorities'][0]
        del entry['path']; entry['uri'] = 'https://example.invalid/no-fetch'
        self.save('authority.json', doc)
        report = self.invoke('verify_authority', '--manifest', 'authority.json', '--target', 'source', code=1)
        self.assertEqual(report['data']['authority_state'], 'AUTHORITY_NOT_VERIFIED')
        entry.pop('uri'); entry['path'] = 'missing.txt'; self.save('authority.json', doc)
        report = self.invoke('verify_authority', '--manifest', 'authority.json', '--target', 'source', code=1)
        self.assertEqual(report['data']['authority_state'], 'AUTHORITY_NOT_VERIFIED')

    def test_04_hash_tamper_is_detected_across_pipeline(self):
        (self.root/'source.txt').write_text('changed\n')
        report = self.invoke('verify_authority', '--manifest', 'authority.json', '--target', 'source', code=1)
        self.assertEqual(report['data']['authority_state'], 'AUTHORITY_HASH_MISMATCH')
        self.invoke('verify_lineage', '--manifest', 'lineage.json', code=1)
        self.audit(code=1)
        self.audit('build_handoff', code=1)

    def test_05_lineage_cycle_missing_parent_edge_and_hash(self):
        original = self.load('lineage.json')
        cases = []
        cycle = json.loads(json.dumps(original)); cycle['nodes'][0]['parents'] = [{'id':'derived','sha256':cycle['nodes'][1]['sha256']}]; cycle['edges'].append({'parent':'derived','child':'source'}); cases.append(cycle)
        missing = json.loads(json.dumps(original)); missing['nodes'][1]['parents'][0]['id'] = 'unknown'; cases.append(missing)
        wrong_hash = json.loads(json.dumps(original)); wrong_hash['nodes'][1]['parents'][0]['sha256'] = '0'*64; cases.append(wrong_hash)
        no_edge = json.loads(json.dumps(original)); no_edge['edges'] = []; cases.append(no_edge)
        duplicate = json.loads(json.dumps(original)); duplicate['nodes'].append(duplicate['nodes'][0]); cases.append(duplicate)
        for index, doc in enumerate(cases):
            with self.subTest(case=index):
                self.save('lineage.json', doc)
                self.invoke('verify_lineage', '--manifest', 'lineage.json', code=1)

    def test_06_protected_sealed_and_substring_false_positives(self):
        for name in ('golden_analysis', 'threshold_results', 'unsealed_data'):
            self.invoke('check_protected_paths', '--operation', 'write', '--path', name)
        self.invoke('check_protected_paths', '--operation', 'read', '--path', 'protected/preserve.txt')
        for operation, path in [('read','sealed/secret.txt'),('read','Sealed/secret.txt'),('write','protected/new.json'),('delete','.'),('write','.'),('rename','protected')]:
            args = ['--operation',operation,'--path',path]
            if operation == 'rename': args += ['--destination','renamed']
            self.invoke('check_protected_paths', *args, code=1)
        self.invoke('check_protected_paths', '--operation','copy','--path','protected/preserve.txt','--destination','derived-copy.txt')
        self.invoke('check_protected_paths', '--operation','copy','--path','sealed/secret.txt','--destination','derived-copy.txt',code=1)

    def test_07_unsafe_paths(self):
        for value in ('../escape','/absolute','C:/absolute',r'\\host\share','file:stream','NUL.txt','bad.','bad ','foo/../bar','foo*'):
            with self.subTest(path=value):
                self.invoke('check_protected_paths','--operation','read','--path',value,code=2)

    def test_08_symlink_is_rejected_for_read_and_output(self):
        (self.root/'alias').symlink_to(self.root/'source.txt')
        self.invoke('check_protected_paths','--operation','read','--path','alias',code=2)
        (self.root/'directory-alias').symlink_to(self.root/'protected', target_is_directory=True)
        self.invoke('check_protected_paths','--operation','write','--path','directory-alias/new.json',code=2)
        (self.root/'broken').symlink_to(self.root/'missing')
        self.invoke('verify_lineage','--manifest','lineage.json','--output','broken',code=2)

    def test_09_sealed_hash_is_blocked_before_read(self):
        doc = self.load('hashes.json'); doc['files'][0]['path'] = 'sealed/secret.txt'; self.save('hashes.json',doc)
        report = self.invoke('verify_hashes','--manifest','hashes.json',code=1)
        self.assertEqual(report['issues'][0]['code'],'sealed_read_forbidden')

    def test_10_json_schema_and_invalid_numbers(self):
        for content in ('{"schema_version":"1","schema_version":"1","files":[]}', '{"value":NaN}', '{"value":1e309}', '{"schema_version":"1","files":[],"typo":1}'):
            (self.root/'bad.json').write_text(content)
            self.invoke('verify_hashes','--manifest','bad.json',code=2)

    def test_11_output_is_create_only_and_dry_run_never_writes(self):
        before = (self.root/'source.txt').read_bytes()
        self.invoke('verify_lineage','--manifest','lineage.json','--output','source.txt',code=1)
        self.assertEqual(before,(self.root/'source.txt').read_bytes())
        self.invoke('verify_lineage','--manifest','lineage.json','--output','new.json','--dry-run')
        self.assertFalse((self.root/'new.json').exists())
        report = self.invoke('verify_lineage','--manifest','lineage.json','--output','new.json')
        self.assertEqual(report,self.load('new.json'))
        self.invoke('verify_lineage','--manifest','lineage.json','--output','new.json',code=1)
        self.invoke('verify_lineage','--manifest','lineage.json','--output','missing/report.json',code=2)
        self.invoke('verify_lineage','--manifest','lineage.json','--output','protected/new.json',code=1)

    def test_12_preflight_never_runs_or_approves(self):
        report = self.preflight('--dry-run')
        self.assertFalse(report['data']['experiment_executed'])
        self.assertFalse(report['data']['approval_granted'])
        self.assertFalse((self.root/'future-result.json').exists())

    def test_13_preflight_settings_and_evidence_fail(self):
        original = self.load('contract.json')
        for field, value in [('retry',1),('fallback',True),('max_input_tokens',4096)]:
            changed = json.loads(json.dumps(original)); changed['inference'][field] = value; self.save('contract.json',changed)
            self.preflight(code=1)
        changed = json.loads(json.dumps(original)); changed['prerequisites'][0]['evidence']['sha256'] = '0'*64; self.save('contract.json',changed)
        self.preflight(code=1)

    def test_14_scientific_required_blocks_without_claiming_approval(self):
        doc = self.load('contract.json'); doc['audit_required_layers'].append('scientific_status'); self.save('contract.json',doc); self.rebind_receipt()
        report = self.audit(code=1)
        self.assertEqual(report['data']['layers']['scientific_status'],'NOT_ASSESSED')
        self.assertFalse(report['data']['approval_granted'])

    def test_15_structural_validation_checks_actual_artifact(self):
        self.save('result.json',{'answer':'WRONG'})
        doc = self.load('receipt.json'); doc['outputs'][0]['sha256'] = digest(self.root/'result.json'); self.save('receipt.json',doc)
        report = self.audit(code=1)
        self.assertEqual(report['data']['layers']['persistence_status'],'PASS')
        self.assertEqual(report['data']['layers']['structural_status'],'FAIL')

    def test_16_remote_schema_reference_is_rejected(self):
        self.save('result.schema.json',{'$ref':'https://example.invalid/never-fetch'})
        self.audit(code=2)

    def test_17_output_schema_hash_is_bound(self):
        self.save('result.schema.json',{})
        report = self.audit(code=1)
        self.assertEqual(report['data']['layers']['structural_status'],'FAIL')

    def test_18_receipt_contract_and_count_are_bound(self):
        doc = self.load('receipt.json'); doc['contract_sha256'] = '0'*64; doc['request_count'] = 99; self.save('receipt.json',doc)
        report = self.audit(code=1)
        self.assertEqual(report['data']['layers']['execution_status'],'FAIL')

    def test_19_audit_can_read_protected_output_and_past_runtime(self):
        contract = self.load('contract.json'); contract['runtime']['python'] = '3.9.99'; self.save('contract.json',contract)
        receipt = self.load('receipt.json'); receipt['runtime'] = contract['runtime']; self.save('receipt.json',receipt); self.rebind_receipt()
        policy = self.load('policy.json'); policy['protected_files'].append('result.json'); self.save('policy.json',policy)
        self.audit()

    def test_20_handoff_has_restart_information(self):
        text = self.audit('build_handoff','--format','markdown',raw=True).decode('utf-8')
        for expected in ('authority.path: source.txt','contract: contract.json','Next action','Stop boundary','NOT_ASSESSED','Approval granted: no.'):
            self.assertIn(expected,text)

    def test_21_cli_error_is_json_exit_two(self):
        self.invoke('verify_lineage',code=2)

    def test_22_git_commit_is_not_an_unverified_nonempty_string(self):
        contract = self.load('contract.json'); contract['git_commit'] = 'a'*40; self.save('contract.json',contract)
        report = self.preflight(code=1)
        self.assertTrue(any(check['name']=='code.git_commit' and check['status']=='FAIL' for check in report['checks']))

    def test_23_nonzero_temperature_is_preserved(self):
        contract = self.load('contract.json'); contract['inference']['temperature']=0.7; contract['inference']['top_p']=0.95; self.save('contract.json',contract)
        self.preflight()


    def test_24_blocked_handoff_is_saved_without_overwrite(self):
        doc = self.load('contract.json'); doc['audit_required_layers'].append('scientific_status'); self.save('contract.json',doc); self.rebind_receipt()
        report = self.audit('build_handoff','--output','blocked.json',code=1)
        self.assertEqual(report,self.load('blocked.json'))
        self.assertEqual(report['status'],'blocked')
        self.audit('build_handoff','--output','blocked.json',code=1)

    def test_25_failed_receipt_with_no_outputs_is_a_valid_blocked_run(self):
        doc = self.load('receipt.json'); doc['status']='failed'; doc['outputs']=[]; self.save('receipt.json',doc)
        (self.root/'result.json').unlink()
        report = self.audit(code=1)
        for layer in ('execution_status','persistence_status','structural_status'):
            self.assertEqual(report['data']['layers'][layer],'FAIL')

    def test_26_past_git_commit_does_not_require_current_head(self):
        contract = self.load('contract.json'); contract['git_commit']='a'*40; self.save('contract.json',contract)
        receipt = self.load('receipt.json'); receipt['git_commit']='a'*40; self.save('receipt.json',receipt); self.rebind_receipt()
        self.audit()
        receipt['git_commit']='b'*40; self.save('receipt.json',receipt)
        report = self.audit(code=1)
        self.assertEqual(report['data']['layers']['execution_status'],'FAIL')

if __name__ == '__main__':
    unittest.main()
