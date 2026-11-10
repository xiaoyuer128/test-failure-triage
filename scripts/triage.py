"""Read-only evidence extraction from bounded UTF-8 JUnit XML and local source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

LIMIT = 2 * 1024 * 1024


def read_text(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Input exceeds 2 MiB')
    return raw.decode('utf-8-sig')


def tag(element):
    return element.tag.rsplit('}', 1)[-1]


def locations(text):
    result = []
    patterns = [r'File "([^"\n]+\.py)", line (\d+)', r'^\s*([^\n]+?\.py):(\d+):']
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            item = {'path':match.group(1).strip(), 'line':int(match.group(2))}
            if item not in result:
                result.append(item)
    return result[:50]


def source_context(root, location):
    name = location['path']
    # Portable report paths must not escape the selected source tree.
    if '\\' in name:
        name = name.replace('\\','/')
    path = Path(name)
    if re.match(r'^[A-Za-z]:',name) and not path.is_absolute():
        return {'status':'foreign_absolute_path'}
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root):
        return {'status':'outside_source_root'}
    try:
        text = read_text(candidate)
        lines = text.splitlines()
        line = location['line']
        if line < 1 or line > len(lines):
            return {'status':'line_out_of_range'}
        return {'status':'available','relative_path':candidate.relative_to(root).as_posix(), 'line':line,'excerpt':[{'line':i+1,'text':lines[i]} for i in range(max(0,line-2), min(len(lines),line+1))], 'sha256':hashlib.sha256(text.encode()).hexdigest(), 'version_match':'unknown'}
    except (OSError,UnicodeError,ValueError):
        return {'status':'unavailable'}


def signals(text):
    checks = [('import',r'\b(?:ModuleNotFoundError|ImportError)\b'),('timeout',r'\b(?:TimeoutError|ReadTimeout|ConnectTimeout)\b'),('assertion',r'\bAssertionError\b|assert '),('permission',r'\bPermissionError\b'),('connection',r'\b(?:ConnectionError|ConnectionRefusedError)\b')]
    return [name for name,pattern in checks if re.search(pattern,text)] or ['unclassified']


def verification_plan(evidence):
    rules = {
        'import':('Dependency or import-path mismatch','Compare the failed environment dependency versions and import path with the expected project configuration'),
        'timeout':('Slow dependency, timing or timeout-budget mismatch','Inspect timestamps and external-service availability before changing timeout limits'),
        'assertion':('Product behavior or test expectation mismatch','Compare actual and expected values with the documented contract before changing either code or assertion'),
        'permission':('Filesystem or execution permission mismatch','Check the exact denied resource and effective identity; do not broaden permissions blindly'),
        'connection':('Dependency unavailable or endpoint mismatch','Verify configured host/port and dependency state without assuming a product defect'),
        'unclassified':('Insufficient evidence for classification','Inspect full failure text and the first relevant project frame')}
    plans=[]
    for index,item in enumerate(evidence):
        for signal in item['signals']:
            hypothesis,check=rules[signal]
            plans.append({'evidence_index':index,'signal':signal,'hypothesis':hypothesis,'confidence':'unconfirmed','verification':check})
    return plans


def analyze(report, source_root, log=None):
    root = Path(source_root).resolve()
    if not root.is_dir(): raise ValueError('Source root must be an existing directory')
    raw = read_text(report)
    if re.search(r'<!\s*(?:DOCTYPE|ENTITY)',raw,re.IGNORECASE):
        raise ValueError('DTD and entity declarations are unsupported')
    xml = ET.fromstring(raw)
    if tag(xml) not in ('testsuite','testsuites'):
        raise ValueError('Expected testsuite or testsuites root')
    records, counts, warnings = [], {'passed':0,'failed':0,'error':0,'skipped':0}, []
    cases = [element for element in xml.iter() if tag(element)=='testcase']
    if len(cases)>5000: raise ValueError('Maximum 5000 testcases')
    for index, case in enumerate(cases):
        children=list(case)
        failures=[e for e in children if tag(e) in ('failure','error')]
        if not failures:
            counts['skipped' if any(tag(e)=='skipped' for e in children) else 'passed'] += 1
            continue
        counts['error' if any(tag(e)=='error' for e in failures) else 'failed'] += 1
        evidence=[]
        for failure in failures:
            text=''.join(failure.itertext())
            refs=locations(text)
            evidence.append({'kind':tag(failure),'reported_type':failure.get('type'), 'message':failure.get('message',''), 'text':text[:16000], 'text_truncated':len(text)>16000, 'signals':signals(failure.get('message','')+'\n'+text), 'locations':[{**ref,'source':source_context(root,ref)} for ref in refs]})
        captured=[]
        for child in children:
            if tag(child) in ('system-out','system-err'):
                text=''.join(child.itertext())
                captured.append({'stream':tag(child),'text':text[:8000],'truncated':len(text)>8000,'attribution':'testcase-local; relevance unverified'})
        records.append({'record_id':index+1,'name':case.get('name',''), 'classname':case.get('classname',''),'evidence':evidence,'captured_output':captured,'root_cause':'unconfirmed','verification_plan':verification_plan(evidence),'unknowns':['Report/checkout version match','Whether failure reproduces in the same environment','Whether test or product violates its intended contract'],'next_steps':['Verify report and checkout versions match','Inspect cited frames and assertion values','Review a targeted rerun before executing it']})
    for suite in (e for e in xml.iter() if tag(e)=='testsuite'):
        descendants = [e for e in suite.iter() if tag(e)=='testcase']
        for attribute, kinds in (('failures',('failure',)),('errors',('error',))):
            declared = suite.get(attribute)
            actual = sum(any(tag(child) in kinds for child in case) for case in descendants)
            if declared is not None:
                try:
                    if int(declared)!=actual:
                        warnings.append('Suite declared '+attribute+' count differs from testcase evidence')
                except ValueError:
                    warnings.append('Suite has noninteger '+attribute+' count')
        if any(tag(e) in ('failure','error') for e in suite):
            warnings.append('Suite-level failure/error is not a testcase; inspect original report')
    if not cases: warnings.append('No testcase records; not proof of a successful run')
    log_context = None
    if log is not None:
        text=read_text(log)
        log_context={'tail':text[-8000:],'truncated':len(text)>8000,'attribution':'unassigned; not used as testcase evidence'}
    return {'report_version':'1.0','summary':{**counts,'total':len(cases)},'failures':records,'warnings':sorted(set(warnings)), 'log_context':log_context,'claims':{'root_causes_confirmed':False,'flakiness_assessed':False}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',required=True)
    parser.add_argument('--source-root',required=True)
    parser.add_argument('--log')
    parser.add_argument('--output')
    args=parser.parse_args()
    try:
        if args.output:
            target=Path(args.output).resolve()
            if target.exists(): raise ValueError('Output already exists; choose a new file')
            if target in [Path(p).resolve() for p in (args.report,args.log) if p]: raise ValueError('Output must not overwrite inputs')
        result=analyze(args.report,args.source_root,args.log)
        output=json.dumps(result,ensure_ascii=True,indent=2)
        if args.output:
            with Path(args.output).open('x',encoding='utf-8') as stream: stream.write(output+'\n')
        print(output)
        return 0
    except (ValueError,OSError,UnicodeError,ET.ParseError,RecursionError) as exc:
        print(json.dumps({'error':str(exc)},ensure_ascii=True))
        return 2


if __name__=='__main__': raise SystemExit(main())
