import requests
import sys
import json
import traceback
import jsonschema
import threading
import time
import hashlib
import binascii
import re
from Crypto.Cipher import AES
from http.server import HTTPServer, BaseHTTPRequestHandler

admin_stuff_schema = json.load(open('www/schemas/admin_stuff'))
credentials_schema = json.load(open('www/schemas/credentials'))
empty_schema = json.load(open('www/schemas/empty'))
lkb_666_summary_schema = json.load(open('www/schemas/lkb_666_summary'))
fb_token_schema = json.load(open('www/schemas/fb_token'))

re_boring = re.compile(r'127.0.0.1 - - \[[0-9]{2}\/[A-Z][a-z]+\/[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\] "GET \/api\/shenanigans\/lkb-666\/summary HTTP\/1.0" 200 -')

def read_json_file(filename, schema):
	with open(filename) as file:
		obj = json.load(file)
		jsonschema.validate(obj, schema)
		return obj

def write_json_file(filename, schema, obj):
	jsonschema.validate(obj, schema)
	with open(filename,'w') as file:
		json.dump(obj, file)

class StatusCodeException(Exception):
	def __init__(self, code):
		Exception.__init__(self,'Unexpected http status code: ' + str(code))

class Datastore():
	def __init__(self):
		self.stuff = None
		self.reactions = None

	def set_stuff(self, stuff):
		self.stuff = stuff

	def get_stuff(self):
		return self.stuff

	def get_reactions(self):
		return self.reactions

	def set_reactions(self, reactions, timestamp, epistemic_status):
		self.reactions = {"summary":reactions['summary'], "timestamp":timestamp, "epistemicStatus": epistemic_status}

	def empty_summary(self):
		return {'like':0,'love':0,'haha':0,'wow':0,'sad':0,'angry':0}

class OpenDankHandler(BaseHTTPRequestHandler):
	def json(self, schema, obj):
		jsonschema.validate(obj, schema)
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

	def not_authorized(self):
		self.send_error(401)

	def do_GET(self):
		if self.path == '/api/shenanigans/lkb-666/summary':
			reactions = self.db().get_reactions()
			if reactions == None:
				result = {"meta":{"epistemicStatus":"missing"}}
			else:
				result = {"meta":{"epistemicStatus":reactions['epistemicStatus'],"lastUpdated":reactions['timestamp']}, "summary":reactions['summary']}
			self.json(lkb_666_summary_schema, result)
		else:
			self.not_found()

	def read_json(self,schema):
		content_length = int(self.headers['Content-Length'])
		json_input = str(self.rfile.read(content_length), 'utf-8')
		obj = json.loads(json_input)
		jsonschema.validate(obj, schema)
		return obj

	def hash(self, password, salt):
		passwordb = bytes(password, 'ascii')
		saltb = binascii.unhexlify(salt)
		dk = hashlib.pbkdf2_hmac('sha256', passwordb, saltb, 100000)
		return str(binascii.hexlify(dk), 'ascii')

	def handle_admin_stuff(self):
		credentials = read_json_file('credentials.json', credentials_schema)
		obj = self.read_json(admin_stuff_schema)
		hashed = self.hash(obj['password'],credentials['salt'])
		if obj['username'] != credentials['username']:
			self.not_authorized()
			print('Admin auth failure: incorrect username')
			return
		if hashed != credentials['pwhash']:
			self.not_authorized()
			print('Admin auth failure: incorrect password')
			return
		print('Checking validity of admin token')
		token = obj['token']
		postId = obj['postId']
		try:
			self.try_getting_some_reactions(token, postId)
		except StatusCodeException:
			print('Could not set token, it\'s probably wrong')
			self.bad_request()
			return

		app_id = credentials['appId']
		app_secret = self.decrypt(obj['password'], credentials['appSecretEnc'])

		print('Converting to long token')
		long_token = self.convert_to_long_token(app_id, app_secret, token)
		try:
			self.try_getting_some_reactions(long_token, postId)
		except StatusCodeException:
			print('Long token appeared not to work for some reason??')
			self.internal_error()
			return

		real_post = credentials['realPostId'] == postId
		poll_interval = obj['pollInterval']

		stuff = {"appId":app_id, "appSecret":app_secret, "token":token, "postId":postId, "pollInterval":poll_interval, "realPost":real_post}
		self.write_token_to_file(stuff)

		self.db().set_stuff(stuff)
		self.json(empty_schema, {})

	def write_token_to_file(self, stuff):
		write_json_file('fb_token', fb_token_schema, stuff)

	def decrypt(self, password, enc):
		key = hashlib.sha256(bytes(password,'ascii')).digest()
		encb = binascii.unhexlify(enc)
		iv = encb[0:16]
		cipher = encb[16:]
		resultb = AES.new(key,AES.MODE_CFB,iv).decrypt(cipher)
		result = str(resultb,'ascii')
		print(result)
		print(enc)
		return result

	def do_POST(self):
		try:
			if self.path == '/api/admin/stuff':
				self.handle_admin_stuff()
			else:
				self.not_found()
		except json.decoder.JSONDecodeError:
			print('Json decode error')
			self.bad_request()
		except jsonschema.exceptions.ValidationError:
			print('Failed schema')
			self.bad_request()
		except Exception:
			traceback.print_exc()
			self.internal_error()

	def convert_to_long_token(self,app_id,app_secret,token):
		url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id='+app_id+'&client_secret='+app_secret+'&fb_exchange_token='+token
		r = requests.get(url)
		if r.status_code != 200:
			print(r.text)
			raise StatusCodeException(r.status_code)

		return r.json()['access_token']

	def try_getting_some_reactions(self,token,postId):
		url = 'https://graph.facebook.com/v2.8/'+postId+'?access_token='+token+'&fields=reactions&format=json&method=get&pretty=0'

		r = requests.get(url)
		if r.status_code != 200:
			print(r.text)
			raise StatusCodeException(r.status_code)
		return r.json()

	def db(self):
		global db
		return db

	# override
	def log_message(self, format, *args):
		if len(args) == 3 and args[0].startswith('GET /api/shenanigans/lkb-666/summary HTTP/') and args[1] == '200' and args[2] == '-':
			# way too many of these requests to want to log them all
			pass
		else:
			print(format % args)

db = None

class PollingThread(threading.Thread):
	def run(self):
		self.try_loading_fb_token()
		self.slow = False
		try:
			print('Starting polling thread')
			while True:
				self.step()
				stuff = self.db().get_stuff()
				if stuff == None:
					time.sleep(1)
				elif self.slow:
					time.sleep(max(60,stuff['pollInterval']))
				else:
					time.sleep(stuff['pollInterval'])
		except KeyboardInterrupt:
			print('Exited with keyboard interrupt')
			sys.exit()

	def try_loading_fb_token(self):
		try:
			obj = read_json_file('fb_token', fb_token_schema)
			self.db().set_stuff(obj)
		except FileNotFoundError:
			print('No fb_token file, you\'ll have to supply one using the admin page')
			pass

	def step(self):
		stuff = self.db().get_stuff()
		if stuff == None:
			return
		timestamp = int(time.time()*1000)
		reactions = self.get_reaction_summaries(stuff['token'], stuff['postId'])
		if reactions != None:
			self.slow = False
			print('updating in db with timestamp ' + str(timestamp))
			epistemic_status = 'plausible' if stuff['realPost'] else 'sandbox'
			self.db().set_reactions(reactions, timestamp, epistemic_status)
		else:
			self.slow = True

	def db(self):
		global db
		return db

	def get_reaction_summaries(self,token,postId):
		fields='reactions.type(LIKE).summary(total_count).as(like),reactions.type(LOVE).summary(total_count).as(love),reactions.type(HAHA).summary(total_count).as(haha),reactions.type(WOW).summary(total_count).as(wow),reactions.type(SAD).summary(total_count).as(sad),reactions.type(ANGRY).summary(total_count).as(angry)'
		url = 'https://graph.facebook.com/v2.8/'+postId+'?access_token='+token+'&fields='+fields
		r = requests.get(url)
		if r.status_code != 200:
			print(r.text)
			return None
		obj = r.json()
		return {
			'summary':{
				'like':obj['like']['summary']['total_count'],
				'love':obj['love']['summary']['total_count'],
				'haha':obj['haha']['summary']['total_count'],
				'wow':obj['wow']['summary']['total_count'],
				'sad':obj['sad']['summary']['total_count'],
				'angry':obj['angry']['summary']['total_count']
			}
		}
		
	def get_all_reactions(self,token,postId):
		result = []
		url = 'https://graph.facebook.com/v2.8/'+postId+'/reactions?access_token='+token+'&format=json&method=get&pretty=0'
		while True:
			r = requests.get(url)
			if r.status_code != 200:
				print(r.text)
				return None
			obj = r.json()
			result += obj['data']
			if 'next' not in obj['paging']:
				return result
			url = obj['paging']['next']


def run():
	global db
	server_address = ('127.0.0.1', 8080)
	db = Datastore()
	PollingThread().start()
	httpd = HTTPServer(server_address, OpenDankHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print('Exited with keyboard interrupt')
		sys.exit()

run()
