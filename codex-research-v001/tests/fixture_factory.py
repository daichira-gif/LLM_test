"""Small synthetic fixture; no research asset is read or copied."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys


def put_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError('Fixture destination must be empty; existing files are never overwritten.')
    (root / 'source.txt').write_text('Synthetic authority: alpha\n', encoding='utf-8')
    (root / 'derived.txt').write_text('Synthetic derived input: ALPHA\n', encoding='utf-8')
    (root / 'code.py').write_text('# Synthetic code identity; never executed.\n', encoding='utf-8')
    (root / 'config.json').write_text('{"mode":"fixture"}\n', encoding='utf-8')
    (root / 'model.txt').write_text('Synthetic model identity; no inference.\n', encoding='utf-8')
    (root / 'prerequisite.txt').write_text('Synthetic prerequisite checked.\n', encoding='utf-8')
    (root / 'sealed').mkdir(exist_ok=True)
    (root / 'sealed' / 'secret.txt').write_text('DO NOT READ\n', encoding='utf-8')
    (root / 'protected').mkdir(exist_ok=True)
    (root / 'protected' / 'preserve.txt').write_text('PRESERVE\n', encoding='utf-8')
    put_json(root / 'policy.json', {'schema_version':'1','protected_roots':['protected'], 'protected_files':[], 'sealed_roots':['sealed'], 'sealed_files':[]})
    def record(identifier, path): return {'id':identifier,'path':path,'sha256':digest(root/path)}
    source = record('source', 'source.txt')
    derived = record('derived', 'derived.txt')
    code, config, model = record('code', 'code.py'), record('config', 'config.json'), record('model', 'model.txt')
    put_json(root/'authority.json', {'schema_version':'1','authorities':[{**source,'role':'input','version':'fixture-v1','state':'current'}]})
    put_json(root/'hashes.json', {'schema_version':'1','files':[source,derived]})
    put_json(root/'lineage.json', {'schema_version':'1','nodes':[{**source,'parents':[]},{**derived,'parents':[{'id':'source','sha256':source['sha256']}]}],'edges':[{'parent':'source','child':'derived'}]})
    schema = {'$schema':'https://json-schema.org/draft/2020-12/schema', 'type':'object','required':['answer'],'properties':{'answer':{'const':'ALPHA'}},'additionalProperties':False}
    put_json(root/'result.schema.json',schema)
    put_json(root/'result.json',{'answer':'ALPHA'})
    contract = {'schema_version':'1','authority':{'id':'source','sha256':source['sha256']},'lineage_sha256':digest(root/'lineage.json'),
                'inputs':[derived], 'code':code, 'config':config, 'model':model,
                'runtime':{'python':'.'.join(map(str,sys.version_info[:3])),'platform':sys.platform},
                'inference':{'temperature':0,'top_p':1,'seed':123,'retry':0,'fallback':False,'context_tokens':4096,'max_input_tokens':1024,'max_output_tokens':128,'request_count':1},
                'outputs':[{'id':'result','path':'result.json','schema':'result.schema.json','schema_sha256':digest(root/'result.schema.json')}],
                'prerequisites':[{'name':'fixture_available','status':'PASS','evidence':{'path':'prerequisite.txt','sha256':digest(root/'prerequisite.txt')}}],
                'audit_required_layers':['execution_status','persistence_status','structural_status']}
    put_json(root/'contract.json',contract)
    receipt = {'schema_version':'1','contract_sha256':digest(root/'contract.json'),'status':'completed',
               'inputs':[derived], 'code':code, 'config':config, 'model':model,
               'runtime':contract['runtime'], 'inference':contract['inference'], 'request_count':1,'outputs':[record('result','result.json')]}
    put_json(root/'receipt.json',receipt)
    return root

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: fixture_factory.py DESTINATION')
    create_fixture(Path(sys.argv[1]))
