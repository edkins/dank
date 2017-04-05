import hashlib
import json
import binascii
import os
import Crypto.Random.random
from Crypto.Cipher import AES

chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

password = ''
for i in range(32):
	password += Crypto.Random.random.choice(chars)
salt = os.urandom(16)

username = input('Enter username: ')
appSecret = bytes(input('Enter appSecret: '), 'ascii')
appId = '312279525854012'

passwordb = bytes(password, 'ascii')
dk = hashlib.pbkdf2_hmac('sha256', passwordb, salt, 100000)
hashed = str(binascii.hexlify(dk),'ascii')
salthex = str(binascii.hexlify(salt),'ascii')

iv = Crypto.Random.new().read(AES.block_size)
key = hashlib.sha256(passwordb).digest()
cipher = AES.new(key, AES.MODE_CFB, iv)
appSecretEnc = str(binascii.hexlify(iv + cipher.encrypt(appSecret)), 'ascii')

print(json.dumps({"username":username,"pwhash":hashed,"salt":salthex,"appId":appId,"appSecretEnc":appSecretEnc}))
print(password)
