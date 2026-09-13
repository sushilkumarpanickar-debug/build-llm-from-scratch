import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location('workspace',Path(__file__).with_name('server.py'))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.DB = Path(self.temp.name)/'workspace.sqlite3'
        app.initialize()
        self.server = app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:'+str(self.server.server_port)
        self.mock = patch.object(app,'ollama',side_effect=lambda path,body=None: {'models':[{'name':'test-local'}]} if path=='tags' else {'message':{'content':'1. Review source notes.\n2. Prepare a draft.'}})
        self.mock.start()
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.mock.stop()
        self.temp.cleanup()
    def request(self,path,data=None,token=app.TOKEN,host=None):
        headers={'Content-Type':'application/json','X-Workspace-Token':token}
        if host: headers['Host']=host
        req=Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        try:
            with urlopen(req) as r: return r.status,json.load(r)
        except HTTPError as e: return e.code,json.load(e)
    def test_notes_persist_and_are_scoped(self):
        self.assertEqual(self.request('/api/notes',{'scope':'Personal','title':'Preference','content':'Prefer concise reports','source':'User'})[0],201)
        app.initialize()
        self.assertEqual(len(self.request('/api/state?scope=Personal')[1]['notes']),1)
        self.assertEqual(self.request('/api/state?scope=SNNS%20Smartact')[1]['notes'],[])
        self.assertEqual(len(app.retrieve('Personal','concise reports')),1)
        self.assertEqual(app.retrieve('SNNS Smartact','concise reports'),[])
    def test_branded_interface_assets_are_served(self):
        with urlopen(self.base + '/') as response:
            page = response.read().decode()
            self.assertIn('SNNS INTELLIGENCE', page)
            self.assertIn('/snns_logo.png', page)
        with urlopen(self.base + '/snns_logo.png') as response:
            self.assertEqual(response.headers.get_content_type(), 'image/png')
            self.assertEqual(response.read(8), b'\x89PNG\r\n\x1a\n')
    def test_write_and_host_protection(self):
        self.assertEqual(self.request('/api/notes',{},token='wrong')[0],403)
        self.assertEqual(self.request('/api/state',host='evil.example')[0],403)
        self.assertEqual(self.request('/api/notes',{'scope':'unknown'})[0],400)
        self.assertEqual(self.request('/api/notes',[])[0],400)
    def test_chat_and_task_lifecycle(self):
        self.assertEqual(self.request('/api/chat',{'prompt':'Hello','model':'test-local'})[0],200)
        self.assertEqual(len(self.request('/api/state')[1]['messages']),2)
        self.assertEqual(self.request('/api/tasks',{'prompt':'Plan a report','model':'test-local'})[0],200)
        task=self.request('/api/state')[1]['tasks'][0]
        self.assertEqual(task['status'],'planned')
        self.assertEqual(self.request('/api/tasks/status',{'scope':'SNNS Smartact','id':task['id'],'status':'completed'})[0],404)
        self.assertEqual(self.request('/api/tasks/status',{'id':task['id'],'status':'completed'})[0],200)
    def test_model_failure_not_saved_as_success(self):
        with patch.object(app,'ollama',side_effect=OSError('Unavailable')):
            self.assertEqual(self.request('/api/chat',{'prompt':'Hello','model':'test-local'})[0],503)
        self.assertEqual(self.request('/api/state')[1]['messages'],[])
    def test_cloud_model_excluded(self):
        with patch.object(app,'ollama',return_value={'models':[{'name':'test-cloud'},{'name':'remote','remote_host':'example.com'},{'name':'local'}]}):
            self.assertEqual(app.models(),['local'])

if __name__=='__main__':unittest.main()
