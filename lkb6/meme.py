import requests
import sys
import json
import traceback
import jsonschema
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

set_token_schema = json.load(open('www/schemas/set_token'))

post_id = '246614445801677_246622789134176'

class StatusCodeException(Exception):
	def __init__(self, code):
		Exception.__init__(self,'Unexpected http status code: ' + str(code))

class Datastore():
	def __init__(self):
		self.token = None
		self.reactions = []
		self.summary = self.empty_summary()

	def set_token(self, token):
		self.token = token

	def get_token(self):
		return self.token

	def get_reactions(self):
		return self.reactions

	def set_reactions(self, reactions):
		self.reactions = reactions
		summary = self.empty_summary()
		for reaction in reactions:
			summary[reaction['type']] += 1
		self.summary = summary

	def get_summary(self):
		return self.summary

	def empty_summary(self):
		return {'LIKE':0,'LOVE':0,'HAHA':0,'WOW':0,'SAD':0,'ANGRY':0}

class OpenDankHandler(BaseHTTPRequestHandler):
	def json(self, obj):
		json_data = json.dumps(obj)
		self.send_response(200)
		self.send_header('Content-Type','application/json')
		self.end_headers()
		self.wfile.write(bytes(json_data,'utf-8'))

	def not_found(self):
		self.send_error(404)

	def internal_error(self):
		self.send_error(500)

	def bad_request(self):
		self.send_error(400)

	def do_GET(self):
		if self.path == '/api/shenanigans/lkb-666/summary':
			summary = self.db().get_summary()
			result = {"meta":{"epistemicStatus":"sandbox"}, "summary":summary}
			self.json(result)
		else:
			self.not_found()

	def read_json(self,schema):
		content_length = int(self.headers['Content-Length'])
		json_input = str(self.rfile.read(content_length), 'utf-8')
		obj = json.loads(json_input)
		jsonschema.validate(obj, set_token_schema)
		return obj

	def handle_set_token(self):
		obj = self.read_json(set_token_schema)
		print('Setting admin token')
		token = obj['token']
		try:
			self.get_reactions(token)
		except StatusCodeException:
			print('Could not set token, it\'s probably wrong')
			self.bad_request()
			return
		self.db().set_token(token)
		self.json({})

	def do_POST(self):
		try:
			if self.path == '/api/shenanigans/lkb-666/token':
				self.handle_set_token()
			else:
				self.not_found()
		except json.decoder.JSONDecodeError:
			self.bad_request()
		except jsonschema.exceptions.ValidationError:
			print('Failed schema')
			self.bad_request()
		except Exception:
			traceback.print_exc()
			self.internal_error()

	def get_reactions(self,token):
		url = 'https://graph.facebook.com/v2.8/'+self.post_id()+'?access_token='+token+'&fields=reactions&format=json&method=get&pretty=0'

		r = requests.get(url)
		if r.status_code != 200:
			print(r.text)
			raise StatusCodeException(r.status_code)
		return r.json()

	def post_id(self):
		global post_id
		return post_id

	def db(self):
		global db
		return db

db = None

class PollingThread(threading.Thread):
	def run(self):
		print('Starting polling thread')
		while True:
			self.step()
			time.sleep(5)

	def step(self):
		token = self.db().get_token()
		if token == None:
			print('Reminder: no token yet')
			return
		reactions = self.get_all_reactions(token)
		self.db().set_reactions(reactions)

	def db(self):
		global db
		return db

	def post_id(self):
		global post_id
		return post_id
		
	def get_all_reactions(self,token):
		result = []
		url = 'https://graph.facebook.com/v2.8/'+self.post_id()+'?access_token='+token+'&fields=reactions&format=json&method=get&pretty=0'
		while True:
			r = requests.get(url)
			if r.status_code != 200:
				print(r.text)
				raise StatusCodeException(r.status_code)
			obj = r.json()
			result += obj['reactions']['data']
			if 'next' not in obj['reactions']['paging']:
				return result
			url = obj['reactions']['paging']['next']


def run():
	global db
	server_address = ('127.0.0.1', 8080)
	db = Datastore()
	PollingThread().start()
	httpd = HTTPServer(server_address, OpenDankHandler)
	httpd.serve_forever()

run()
