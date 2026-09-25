"""Offline, read-only research checks. Reports express consistency, never approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import subprocess
import sys
from typing import Any

import jsonschema
from referencing import Registry
from referencing.exceptions import NoSuchResource, Unresolvable

SCHEMA_DIR = Path(__file__).resolve().parents[2] / 'schemas' / 'research'
LAYERS = ('execution_status', 'persistence_status', 'structural_status', 'semantic_status', 'scientific_status')


class HelperError(Exception):
    def __init__(self, code: str, message: str, path: str | None = None, exit_code: int = 2):
        super().__init__(message)
        self.code, self.message, self.path, self.exit_code = code, message, path, exit_code


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError('non-finite JSON number: ' + value)


def _float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('non-finite JSON number')
    return parsed


def parse_json(content: str, path: str) -> Any:
    try:
        return json.loads(content, object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)
    except (ValueError, UnicodeError) as exc:
        raise HelperError('invalid_json', 'Invalid JSON: ' + str(exc), path) from exc


def relative(value: str) -> str:
    if not value or '\x00' in value or '\\' in value:
        raise HelperError('unsafe_path', 'Expected a root-relative POSIX path.', value)
    posix, windows = PurePosixPath(value), PureWindowsPath(value)
    if posix.is_absolute() or windows.drive or windows.is_absolute() or '..' in posix.parts:
        raise HelperError('unsafe_path', 'Absolute, drive, UNC and parent traversal paths are forbidden.', value)
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    for component in posix.parts:
        if component != '.' and (any(character in component for character in ':<>"|?*') or any(ord(character) < 32 for character in component) or component.endswith(('.', ' ')) or component.split('.')[0].upper() in reserved):
            raise HelperError('unsafe_path', 'Windows device names, alternate data streams and trailing-dot/space aliases are forbidden.', value)
    # Normalization permits a policy root's trailing slash, but never parent traversal.
    return posix.as_posix()


def below(path: str, root: str) -> bool:
    path, root = path.casefold(), root.casefold()
    return root == '.' or path == root or path.startswith(root + '/')


def deny_external_refs(schema: Any):
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key in ('$ref', '$dynamicRef') and (not isinstance(value, str) or not value.startswith('#')):
                raise HelperError('external_schema_ref', 'Only in-document JSON Schema references are allowed.')
            deny_external_refs(value)
    elif isinstance(schema, list):
        for item in schema:
            deny_external_refs(item)


def _no_retrieval(uri):
    raise NoSuchResource(ref=uri)


def validate(instance: Any, schema: dict, path: str):
    deny_external_refs(schema)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema, registry=Registry(retrieve=_no_retrieval))
        errors = sorted(validator.iter_errors(instance), key=lambda e: (str(list(e.absolute_path)), e.message))
    except (jsonschema.SchemaError, Unresolvable) as exc:
        raise HelperError('invalid_schema', 'Invalid or unresolved JSON Schema.', path) from exc
    if errors:
        first = errors[0]
        pointer = '/'.join(str(part) for part in first.absolute_path) or '<root>'
        raise HelperError('schema_mismatch', 'Schema validation failed at ' + pointer + ' (' + str(first.validator) + ').', path)


def builtin_schema(name: str) -> dict:
    try:
        return parse_json((SCHEMA_DIR / (name + '.schema.json')).read_text(encoding='utf-8'), name)
    except OSError as exc:
        raise HelperError('schema_io_error', 'Unable to read bundled schema: ' + name) from exc


class Report:
    def __init__(self, tool: str):
        self.tool, self.checks, self.issues, self.data = tool, [], [], {}

    def check(self, name: str, passed: bool, details: str, code: str | None = None, path: str | None = None,
              failed_status: str = 'FAIL') -> bool:
        self.checks.append({'name': name, 'status': 'PASS' if passed else failed_status, 'details': details})
        if not passed:
            self.issue(code or name, details, path)
        return passed

    def issue(self, code: str, message: str, path: str | None = None):
        item = {'code': code, 'message': message}
        if path is not None:
            item['path'] = path
        self.issues.append(item)

    def render(self, exit_code: int | None = None) -> dict:
        if exit_code is None:
            exit_code = 1 if self.issues else 0
        return {'schema_version': '1', 'tool': self.tool,
                'status': 'error' if exit_code == 2 else ('blocked' if exit_code else 'pass'),
                'technical_pass': exit_code == 0, 'checks': self.checks, 'issues': self.issues, 'data': self.data}


class Context:
    def __init__(self, root: str, policy: str):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise HelperError('invalid_root', 'Root must be an existing directory.')
        self.policy = {key: [] for key in ('protected_roots', 'protected_files', 'sealed_roots', 'sealed_files')}
        self.policy_path = relative(policy)
        value = self.read_json(policy, 'protection_policy')
        self.policy = {key: sorted({relative(item) for item in value[key]}) for key in self.policy}
        # Validate existing ancestors, including declarations that are not read by this invocation.
        for entries in self.policy.values():
            for entry in entries:
                self.resolve(entry)
        self.assert_read(self.policy_path)

    def resolve(self, value: str) -> Path:
        normalized = relative(value)
        path = self.root
        for part in PurePosixPath(normalized).parts:
            if part == '.':
                continue
            path = path / part
            if path.is_symlink():
                raise HelperError('symlink_forbidden', 'Symlinks are not supported for inputs or outputs.', value)
        try:
            path.resolve(strict=False).relative_to(self.root)
        except (ValueError, RuntimeError) as exc:
            raise HelperError('unsafe_path', 'Path escapes the selected root.', value) from exc
        return path

    def protected(self, value: str, sealed_only: bool = False, ancestor: bool = False) -> bool:
        path = relative(value)
        groups = ('sealed',) if sealed_only else ('sealed', 'protected')
        for group in groups:
            for root in self.policy[group + '_roots']:
                if below(path, root) or (ancestor and below(root, path)):
                    return True
            for item in self.policy[group + '_files']:
                if path.casefold() == item.casefold() or (ancestor and below(item, path)):
                    return True
        return False

    def assert_read(self, value: str, ancestor: bool = False):
        self.resolve(value)
        if self.protected(value, sealed_only=True, ancestor=ancestor):
            raise HelperError('sealed_read_forbidden', 'Sealed paths may not be read or hashed.', value, 1)

    def assert_write(self, value: str, ancestor: bool = False):
        self.resolve(value)
        if self.protected(value, ancestor=ancestor):
            raise HelperError('protected_write_forbidden', 'Protected or sealed paths may not be modified.', value, 1)

    def bytes(self, value: str) -> bytes:
        self.assert_read(value)
        path = self.resolve(value)
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                raise HelperError('not_regular_file', 'Expected a regular file.', value)
            return path.read_bytes()
        except OSError as exc:
            raise HelperError('input_io_error', 'Cannot read input file.', value) from exc

    def digest(self, value: str) -> str:
        self.assert_read(value)
        path = self.resolve(value)
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                raise HelperError('not_regular_file', 'Expected a regular file.', value)
            result = hashlib.sha256()
            with path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    result.update(chunk)
            return result.hexdigest()
        except FileNotFoundError as exc:
            raise HelperError('artifact_missing', 'Artifact is missing.', value, 1) from exc
        except OSError as exc:
            raise HelperError('input_io_error', 'Cannot hash input file.', value) from exc

    def read_json(self, value: str, schema_name: str | None = None) -> Any:
        try:
            data = parse_json(self.bytes(value).decode('utf-8'), value)
        except UnicodeError as exc:
            raise HelperError('invalid_encoding', 'Expected UTF-8 JSON.', value) from exc
        if schema_name:
            validate(data, builtin_schema(schema_name), value)
        return data

    def fresh_output(self, value: str):
        self.assert_write(value)
        path = self.resolve(value)
        if path.exists() or path.is_symlink():
            raise HelperError('output_exists', 'Output must be new; overwriting is forbidden.', value, 1)
        if not path.parent.is_dir():
            raise HelperError('output_parent_missing', 'Output parent directory must already exist.', value)
        return path

    def save(self, value: str, content: bytes):
        path = self.fresh_output(value)
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
            fd = os.open(path, flags, 0o600)
            with os.fdopen(fd, 'wb') as handle:
                handle.write(content)
        except FileExistsError as exc:
            raise HelperError('output_exists', 'Output was created concurrently; overwriting is forbidden.', value, 1) from exc
        except OSError as exc:
            raise HelperError('output_io_error', 'Unable to create output file.', value) from exc


def hash_record(ctx: Context, item: dict, report: Report, prefix: str) -> bool:
    try:
        actual = ctx.digest(item['path'])
    except HelperError as exc:
        if exc.code == 'artifact_missing':
            return report.check(prefix + '.' + item['id'], False, 'Artifact is unavailable; hash is not verified.',
                                'artifact_unverified', item['path'], 'NOT_VERIFIED')
        raise
    return report.check(prefix + '.' + item['id'], actual == item['sha256'],
                        'Actual artifact hash matches declaration.' if actual == item['sha256'] else 'Artifact SHA-256 mismatch.',
                        'hash_mismatch', item['path'])


def unique_records(records: list[dict], report: Report, prefix: str) -> bool:
    ids, paths = [r['id'] for r in records], [relative(r['path']).casefold() for r in records]
    return (report.check(prefix + '.unique_ids', len(ids) == len(set(ids)), 'Artifact IDs must be unique.')
            & report.check(prefix + '.unique_paths', len(paths) == len(set(paths)), 'Artifact paths must be unique.'))


def authority_check(ctx: Context, manifest: str, target: str, role: str | None, version: str | None, report: Report):
    doc = ctx.read_json(manifest, 'authority_manifest')
    matches = [entry for entry in doc['authorities'] if entry['id'] == target
               and (role is None or entry.get('role') == role) and (version is None or entry.get('version') == version)]
    candidates = [entry for entry in matches if entry['state'] == 'current']
    report.data['authority_state'] = 'AUTHORITY_NOT_VERIFIED'
    if len(candidates) != 1:
        state = ('AUTHORITY_AMBIGUOUS' if len(candidates) > 1 else
                 'AUTHORITY_NOT_FOUND' if not matches else
                 'AUTHORITY_SUPERSEDED' if all(entry['state'] == 'retired' for entry in matches) else
                 'AUTHORITY_NOT_VERIFIED')
        report.data['authority_state'] = state
        report.check('authority.unique_current', False,
                     'Exactly one explicitly current authority must match the requested ID and filters: ' + state + '.',
                     state.lower(), failed_status='NOT_VERIFIED')
        return None
    report.check('authority.unique_current', True, 'Exactly one explicitly current authority matches the requested ID and filters.')
    item = candidates[0]
    if 'uri' in item:
        report.check('authority.local', False, 'Remote authority is not fetched and remains unverified.',
                     'remote_authority_unverified', failed_status='NOT_VERIFIED')
        return None
    if not hash_record(ctx, item, report, 'authority'):
        report.data['authority_state'] = 'AUTHORITY_HASH_MISMATCH' if report.issues[-1]['code'] == 'hash_mismatch' else 'AUTHORITY_NOT_VERIFIED'
        return None
    report.data['authority_state'] = 'AUTHORITY_EXACT'
    return item


def lineage_check(ctx: Context, manifest: str, report: Report):
    doc = ctx.read_json(manifest, 'lineage_manifest')
    if not unique_records(doc['nodes'], report, 'lineage'):
        return doc
    nodes = {node['id']: node for node in doc['nodes']}
    expected = set()
    for node in doc['nodes']:
        hash_record(ctx, node, report, 'lineage.hash')
        parent_ids = [parent['id'] for parent in node['parents']]
        report.check('lineage.parents_unique.' + node['id'], len(parent_ids) == len(set(parent_ids)), 'Expected parents must be unique.')
        for parent in node['parents']:
            expected.add((parent['id'], node['id']))
            exists = parent['id'] in nodes
            report.check('lineage.parent_exists.' + node['id'] + '.' + parent['id'], exists, 'Every expected parent must be declared.')
            if exists:
                report.check('lineage.parent_hash.' + node['id'] + '.' + parent['id'],
                             parent['sha256'] == nodes[parent['id']]['sha256'], 'Expected parent hash must equal its declared, checked hash.')
    edges = [(edge['parent'], edge['child']) for edge in doc['edges']]
    report.check('lineage.edges_unique', len(edges) == len(set(edges)), 'Lineage edges must be unique.')
    report.check('lineage.expected_edges', set(edges) == expected, 'Edges must exactly match every node\'s expected parents.')
    known = all(parent in nodes and child in nodes for parent, child in edges)
    report.check('lineage.edge_nodes', known, 'Every edge endpoint must be declared.')
    # Kahn's algorithm avoids recursion limits and handles disconnected components.
    indegree = {key: 0 for key in nodes}
    children = {key: set() for key in nodes}
    for parent, child in set(edges) | expected:
        if parent in nodes and child in nodes:
            children[parent].add(child)
            indegree[child] += 1
    queue = sorted(key for key, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        key = queue.pop(0)
        visited += 1
        for child in sorted(children[key]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
        queue.sort()
    report.check('lineage.acyclic', visited == len(nodes), 'Lineage must be acyclic, including expected-parent declarations.')
    return doc


def local_runtime() -> dict:
    return {'python': '.'.join(str(part) for part in sys.version_info[:3]), 'platform': sys.platform}


def contract_checks(ctx: Context, contract: dict, report: Report, fresh: bool):
    records = contract['inputs'] + [contract[key] for key in ('code', 'config', 'model')]
    unique_records(records, report, 'contract')
    for item in records:
        hash_record(ctx, item, report, 'contract.hash')
    if fresh:
        report.check('runtime.exact', contract['runtime'] == local_runtime(),
                     'Declared Python version and platform must match this checking runtime.')
    inference = contract['inference']
    report.check('inference.retry_zero', inference['retry'] == 0, 'Retry must be zero.')
    report.check('inference.no_fallback', inference['fallback'] is False, 'Fallback must be disabled.')
    report.check('inference.context', inference['max_input_tokens'] + inference['max_output_tokens'] <= inference['context_tokens'],
                 'Declared maximum input plus output tokens must fit context; tokenization itself is not verified.')
    names = [entry['name'] for entry in contract['prerequisites']]
    report.check('prerequisites.unique', len(names) == len(set(names)), 'Prerequisite names must be unique.')
    for entry in contract['prerequisites']:
        report.check('prerequisite.' + entry['name'], entry['status'] == 'PASS',
                     'Prerequisite must be explicitly PASS with hash-bound evidence.', failed_status='NOT_VERIFIED')
        hash_record(ctx, {'id': entry['name'], **entry['evidence']}, report, 'prerequisite.evidence')
    outputs = contract['outputs']
    unique_records(outputs, report, 'contract.outputs')
    input_paths = {relative(item['path']).casefold() for item in records}
    for entry in outputs:
        report.check('output.distinct.' + entry['id'], relative(entry['path']).casefold() not in input_paths,
                     'Output path must differ from every input/code/config/model path.')
        if fresh:
            ctx.assert_write(entry['path'])
        hash_record(ctx, {'id': entry['id'], 'path': entry['schema'], 'sha256': entry['schema_sha256']}, report, 'output.schema_hash')
        schema = ctx.read_json(entry['schema'])
        deny_external_refs(schema)
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
        except jsonschema.SchemaError as exc:
            raise HelperError('invalid_schema', 'Invalid output JSON Schema.', entry['schema']) from exc
        if fresh:
            ctx.fresh_output(entry['path'])
    if fresh and 'git_commit' in contract:
        # Fixed read-only argv; no hooks, shell, index refresh, checkout or repository mutation.
        try:
            result = subprocess.run(['git', '-c', 'core.fsmonitor=false', 'rev-parse', '--show-toplevel', '--verify', 'HEAD'],
                                    cwd=ctx.resolve(contract['code']['path']).parent, capture_output=True, text=True, check=False, timeout=10,
                                    env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
            lines = result.stdout.strip().splitlines()
            git_root = Path(lines[0]).resolve() if result.returncode == 0 and len(lines) == 2 else None
            within_root = git_root is not None and (git_root == ctx.root or ctx.root in git_root.parents)
            actual = lines[1] if within_root else None
        except (OSError, subprocess.TimeoutExpired):
            actual = None
        report.check('code.git_commit', actual == contract['git_commit'], 'Declared Git commit must match HEAD of the repository containing the code file within the selected root.')


def bind_contract(ctx: Context, contract: dict, authority: dict | None, lineage: dict, lineage_path: str, report: Report):
    report.check('contract.authority_binding', authority is not None and
                 contract['authority'] == {'id': authority['id'], 'sha256': authority['sha256']},
                 'Contract authority must match the uniquely verified authority.')
    report.check('contract.lineage_binding', ctx.digest(lineage_path) == contract['lineage_sha256'],
                 'Contract must bind the exact lineage manifest bytes.')
    nodes = {node['id']: node for node in lineage['nodes']}
    if authority is not None:
        node = nodes.get(authority['id'])
        report.check('lineage.authority_binding', node is not None and all(node.get(key) == authority.get(key) for key in ('id', 'path', 'sha256')),
                     'Verified authority must be represented exactly in the lineage graph.')
    for entry in contract['inputs']:
        node = nodes.get(entry['id'])
        report.check('lineage.input_binding.' + entry['id'], node is not None and
                     all(node.get(key) == entry[key] for key in ('id', 'path', 'sha256')),
                     'Every contract input must match a checked lineage node.')


def run_audit(ctx: Context, args, report: Report):
    authority = authority_check(ctx, args.authority, args.target, args.role, args.version, report)
    lineage = lineage_check(ctx, args.lineage, report)
    contract = ctx.read_json(args.contract, 'experiment_contract')
    receipt = ctx.read_json(args.receipt, 'execution_receipt')
    contract_checks(ctx, contract, report, fresh=False)
    bind_contract(ctx, contract, authority, lineage, args.lineage, report)
    contract_hash = ctx.digest(args.contract)
    report.check('receipt.contract_binding', receipt['contract_sha256'] == contract_hash, 'Receipt must bind the exact contract bytes.')
    execution_checks = [receipt['status'] == 'completed', receipt['runtime'] == contract['runtime'],
                        receipt['inference'] == contract['inference'], receipt['request_count'] == contract['inference']['request_count'],
                        receipt.get('git_commit') == contract.get('git_commit')]
    for key in ('inputs', 'code', 'config', 'model'):
        execution_checks.append(receipt[key] == contract[key])
    execution = all(execution_checks)
    report.check('receipt.execution_consistency', execution, 'Completion, settings, count and input declarations must match the contract; execution itself is not observed.')
    start = len(report.issues)
    unique_records(receipt['outputs'], report, 'receipt.outputs')
    by_id = {entry['id']: entry for entry in receipt['outputs']}
    declared = {entry['id']: entry for entry in contract['outputs']}
    report.check('receipt.output_set', set(by_id) == set(declared), 'Receipt and contract must list exactly the same output IDs.')
    for entry in receipt['outputs']:
        item = declared.get(entry['id'])
        report.check('receipt.output_path.' + entry['id'], item is not None and relative(item['path']) == relative(entry['path']),
                     'Output path must match the contract.')
        hash_record(ctx, entry, report, 'receipt.output_hash')
    persistence = len(report.issues) == start
    structural = set(by_id) == set(declared)
    for entry in contract['outputs']:
        try:
            instance = ctx.read_json(entry['path'])
            schema = ctx.read_json(entry['schema'])
            if ctx.digest(entry['schema']) != entry['schema_sha256']:
                structural = False
            validate(instance, schema, entry['path'])
            report.check('structural.' + entry['id'], True, 'Actual output JSON validates against the declared local schema.')
        except HelperError as exc:
            if exc.code in ('schema_mismatch', 'invalid_json', 'invalid_encoding', 'input_io_error'):
                structural = False
                report.check('structural.' + entry['id'], False, exc.message, exc.code, exc.path)
            else:
                raise
    layers = dict(zip(LAYERS, ['PASS' if execution else 'FAIL', 'PASS' if persistence else 'FAIL',
                             'PASS' if structural else 'FAIL', 'NOT_ASSESSED', 'NOT_ASSESSED']))
    for layer in contract['audit_required_layers']:
        report.check('audit.required.' + layer, layers[layer] == 'PASS',
                     'Required audit layer must be PASS; semantic/scientific layers are not evaluated by V001.',
                     'required_layer_unverified', failed_status=layers[layer])
    report.data = {'layers': layers, 'required_layers': contract['audit_required_layers'],
                   'execution_observation': 'receipt_declared_not_independently_observed', 'approval_granted': False,
                   'authority_state': report.data['authority_state'], 'authority': authority, 'lineage_sha256': ctx.digest(args.lineage), 'contract_sha256': contract_hash,
                   'receipt_sha256': ctx.digest(args.receipt)}
    return contract


def markdown_handoff(report: Report) -> str:
    data = report.data
    lines = ['# Research handoff', '', 'Technical status: ' + ('BLOCKED' if report.issues else 'PASS'),
             'Execution: receipt-declared; not independently observed.', 'Approval granted: no.', '', '## Audit layers', '']
    for layer in LAYERS:
        lines.append('- ' + layer + ': ' + data['layers'][layer])
    lines.extend(['', '## Artifact bindings', ''])
    authority = data.get('authority')
    if authority:
        for key in ('id', 'path', 'role', 'version', 'sha256'):
            if key in authority:
                lines.append('- authority.' + key + ': ' + str(authority[key]))
    for key, value in sorted(data['source_paths'].items()):
        lines.append('- ' + key + ': ' + value)
    for key in ('lineage_sha256', 'contract_sha256', 'receipt_sha256'):
        lines.append('- ' + key + ': `' + data[key] + '`')
    lines.extend(['', '## Unresolved items', '', '- Semantic and scientific validity remain NOT_ASSESSED.'])
    lines.extend(['', '## Next action', '', data['next_action'], '', '## Stop boundary', '', data['stop_boundary'], ''])
    for issue in report.issues:
        lines.append('- ' + issue['code'] + ': ' + issue['message'].replace('\n', ' '))
    return '\n'.join(lines) + '\n'


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise HelperError('invalid_arguments', message)


def parser(tool: str):
    p = Parser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--policy', required=True, help='Root-relative exact-path protection policy JSON.')
    p.add_argument('--output', help='Create this new root-relative report file; never overwrite.')
    p.add_argument('--dry-run', action='store_true', help='Perform checks but never create an output file.')
    if tool in ('verify_authority', 'verify_hashes', 'verify_lineage'):
        p.add_argument('--manifest', required=True)
    if tool in ('verify_authority', 'audit_result', 'build_handoff', 'experiment_preflight'):
        p.add_argument('--target', required=True)
        p.add_argument('--role')
        p.add_argument('--version')
    if tool in ('audit_result', 'build_handoff', 'experiment_preflight'):
        p.add_argument('--authority', required=True)
        p.add_argument('--lineage', required=True)
        p.add_argument('--contract', required=True)
    if tool in ('audit_result', 'build_handoff'):
        p.add_argument('--receipt', required=True)
    if tool == 'build_handoff':
        p.add_argument('--format', choices=('json', 'markdown'), default='json')
    if tool == 'check_protected_paths':
        p.add_argument('--operation', required=True, choices=('read', 'write', 'delete', 'rename', 'copy'))
        p.add_argument('--path', required=True)
        p.add_argument('--destination')
    return p


def dispatch(tool: str, ctx: Context, args, report: Report):
    if tool == 'verify_authority':
        report.data['authority'] = authority_check(ctx, args.manifest, args.target, args.role, args.version, report)
    elif tool == 'verify_hashes':
        doc = ctx.read_json(args.manifest, 'hash_manifest')
        unique_records(doc['files'], report, 'hash_manifest')
        for entry in doc['files']:
            hash_record(ctx, entry, report, 'hash')
    elif tool == 'verify_lineage':
        doc = lineage_check(ctx, args.manifest, report)
        report.data['node_count'] = len(doc['nodes'])
    elif tool == 'check_protected_paths':
        operation = args.operation
        if operation in ('rename', 'copy') and args.destination is None:
            raise HelperError('invalid_arguments', 'rename/copy require --destination.')
        if operation not in ('rename', 'copy') and args.destination is not None:
            raise HelperError('invalid_arguments', '--destination is only valid for rename/copy.')
        if operation == 'read':
            ctx.assert_read(args.path, ancestor=True)
        elif operation == 'copy':
            ctx.assert_read(args.path, ancestor=True)
            ctx.assert_write(args.destination, ancestor=True)
        elif operation == 'rename':
            ctx.assert_write(args.path, ancestor=True)
            ctx.assert_write(args.destination, ancestor=True)
        else:
            ctx.assert_write(args.path, ancestor=True)
        report.check('protection', True, 'Requested path operation is outside the declared prohibitions. No operation was executed.')
        report.data = {'operation': operation, 'path': relative(args.path), 'destination': relative(args.destination) if args.destination else None,
                       'operation_executed': False, 'enforcement': 'declarative_check_not_os_access_control'}
    elif tool == 'experiment_preflight':
        authority = authority_check(ctx, args.authority, args.target, args.role, args.version, report)
        lineage = lineage_check(ctx, args.lineage, report)
        contract = ctx.read_json(args.contract, 'experiment_contract')
        contract_checks(ctx, contract, report, fresh=True)
        bind_contract(ctx, contract, authority, lineage, args.lineage, report)
        report.data = {'approval_granted': False, 'experiment_executed': False,
                       'runtime_observed': local_runtime(), 'scope': 'technical_consistency_only; input tokenization and inference runtime execution are not verified'}
    elif tool in ('audit_result', 'build_handoff'):
        run_audit(ctx, args, report)
        if tool == 'build_handoff':
            report.data['source_paths'] = {key: relative(getattr(args, key)) for key in ('authority', 'lineage', 'contract', 'receipt', 'policy')}
            report.data['next_action'] = 'Resolve reported blockers, then assess semantic/scientific validity under an explicit evaluation contract.'
            report.data['stop_boundary'] = 'No execution or approval is granted. Do not modify protected/sealed assets or promote results on these checks alone.'
            report.data['handoff_markdown'] = markdown_handoff(report)
    else:
        raise HelperError('invalid_tool', 'Unknown helper.')


def main(tool: str) -> int:
    report, ctx, args, exit_code, output_valid = Report(tool), None, None, 0, False
    try:
        args = parser(tool).parse_args()
        ctx = Context(args.root, args.policy)
        if args.output:
            ctx.fresh_output(args.output)
            output_valid = True
        dispatch(tool, ctx, args, report)
        exit_code = 1 if report.issues else 0
    except HelperError as exc:
        report.issue(exc.code, exc.message, exc.path)
        exit_code = exc.exit_code
    except OSError:
        report.issue('io_error', 'Unable to access root or input resources.')
        exit_code = 2
    except Exception as exc:
        # Keep machine-readable errors; do not expose file content, stack traces or absolute paths.
        report.issue('internal_error', 'Unexpected checker error: ' + type(exc).__name__)
        exit_code = 2
    content = (json.dumps(report.render(exit_code), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if args is not None and getattr(args, 'format', 'json') == 'markdown' and 'handoff_markdown' in report.data:
        content = report.data['handoff_markdown'].encode('utf-8')
    if args is not None and args.output and not args.dry_run and ctx is not None and output_valid and exit_code in (0, 1):
        try:
            ctx.save(args.output, content)
        except HelperError as exc:
            report.issue(exc.code, exc.message, exc.path)
            exit_code = exc.exit_code
            content = (json.dumps(report.render(exit_code), ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    sys.stdout.buffer.write(content)
    return exit_code
