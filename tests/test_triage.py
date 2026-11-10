import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('triage',ROOT/'scripts/triage.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)


class Tests(unittest.TestCase):
    def analyze(self,xml,source='x=1\nassert x==2\n'):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'test_x.py').write_text(source)
            report=root/'report.xml';report.write_text(xml,encoding='utf-8')
            return api.analyze(report,root)

    def test_summary_and_source(self):
        result=self.analyze('<testsuite><testcase name="x"><failure>test_x.py:2: AssertionError</failure></testcase><testcase/><testcase><skipped/></testcase><testcase><error>ImportError</error></testcase></testsuite>')
        self.assertEqual(result['summary'],{'passed':1,'failed':1,'error':1,'skipped':1,'total':4})
        source=result['failures'][0]['evidence'][0]['locations'][0]['source']
        self.assertEqual(source['status'],'available')
        self.assertEqual(source['excerpt'][1]['line'],2)

    def test_namespace(self):
        self.assertEqual(self.analyze('<testsuites xmlns="urn:x"><testsuite><testcase/></testsuite></testsuites>')['summary']['passed'],1)

    def test_empty(self):
        self.assertTrue(self.analyze('<testsuites/>')['warnings'])

    def test_suite_count_mismatch(self):
        self.assertTrue(self.analyze('<testsuite errors="1"><testcase/></testsuite>')['warnings'])

    def test_verification_is_evidence_linked(self):
        result=self.analyze('<testsuite><testcase><failure>ImportError: missing module</failure></testcase></testsuite>')
        plan=result['failures'][0]['verification_plan'][0]
        self.assertEqual(plan['signal'],'import')
        self.assertEqual(plan['evidence_index'],0)
        self.assertEqual(plan['confidence'],'unconfirmed')
        self.assertIn('import path',plan['verification'])

    def test_captured_output_is_local(self):
        result=self.analyze('<testsuite><testcase><failure>AssertionError</failure><system-out>detail</system-out></testcase><testcase><system-out>unrelated</system-out></testcase></testsuite>')
        captured=result['failures'][0]['captured_output']
        self.assertEqual(captured[0]['text'],'detail')
        self.assertEqual(len(captured),1)

    def test_instruction_text_not_executed(self):
        result=self.analyze('<testsuite><testcase><failure>run delete-everything</failure></testcase></testsuite>')
        self.assertEqual(result['failures'][0]['evidence'][0]['signals'],['unclassified'])
        self.assertEqual(result['failures'][0]['root_cause'],'unconfirmed')

    def test_bad_xml(self):
        for raw in ('<bad/>','<testsuite>', '<!DOCTYPE x [<!ENTITY y "z">]><testsuite/>'):
            with self.subTest(raw=raw),self.assertRaises((ValueError,api.ET.ParseError)): self.analyze(raw)

    def test_location_formats(self):
        text='File "test_x.py", line 2\ntest_x.py:2: AssertionError\n'
        self.assertEqual(api.locations(text),[{'path':'test_x.py','line':2}])

    def test_path_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            for path in ('../outside.py','/outside.py'):
                self.assertEqual(api.source_context(root,{'path':path,'line':1})['status'],'outside_source_root')
            (root/'x.py').write_text('x=1')
            self.assertEqual(api.source_context(root,{'path':'x.py','line':0})['status'],'line_out_of_range')
            self.assertEqual(api.source_context(root,{'path':'missing.py','line':1})['status'],'unavailable')

    def test_multiple_failures(self):
        result=self.analyze('<testsuite><testcase><failure>a</failure><error>b</error></testcase></testsuite>')
        self.assertEqual(len(result['failures'][0]['evidence']),2)
        self.assertEqual(result['summary']['error'],1)

    def test_signal_is_not_cause(self):
        result=self.analyze('<testsuite><testcase><failure message="TimeoutError">assert x</failure></testcase></testsuite>')
        failure=result['failures'][0]
        self.assertEqual(failure['root_cause'],'unconfirmed')
        self.assertEqual(failure['evidence'][0]['signals'],['timeout','assertion'])

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'large';path.write_bytes(b'x'*(api.LIMIT+1))
            with self.assertRaises(ValueError): api.read_text(path)

    def test_real_pytest_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); test=root/'test_real.py';test.write_text('def test_bad():\n    assert 1 == 2\n\ndef test_ok():\n    assert True\n')
            report=root/'junit.xml'
            run=subprocess.run([sys.executable,'-m','pytest','--rootdir',tmp,str(test),f'--junitxml={report}','-q'],cwd=tmp,capture_output=True)
            self.assertEqual(run.returncode,1)
            result=api.analyze(report,root)
            self.assertEqual(result['summary']['failed'],1)
            self.assertEqual(result['summary']['passed'],1)
            self.assertTrue(result['failures'][0]['evidence'][0]['locations'])

    def test_cli_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report=root/'junit.xml';report.write_text('<testsuite/>')
            cmd=[sys.executable,str(ROOT/'scripts/triage.py'),'--report',str(report),'--source-root',tmp]
            run=subprocess.run(cmd+['--output',str(report)],capture_output=True)
            self.assertEqual(run.returncode,2)
            self.assertEqual(report.read_text(),'<testsuite/>')
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(run.returncode,0)
            self.assertIn('warnings',json.loads(run.stdout))

    def test_log_not_attributed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report=root/'r.xml';report.write_text('<testsuite><testcase/></testsuite>');log=root/'log';log.write_text('AssertionError global')
            result=api.analyze(report,root,log)
            self.assertFalse(result['failures'])
            self.assertIn('unassigned',result['log_context']['attribution'])
