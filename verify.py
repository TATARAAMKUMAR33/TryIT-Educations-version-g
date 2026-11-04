content = open('generate_master.py', encoding='utf-8').read()
print('requests in imports:', 'import os, json, time, uuid, re, requests' in content)
print('requests.post in probe:', 'requests.post' in content)
print('req.post remaining:', 'req.post' in content)
