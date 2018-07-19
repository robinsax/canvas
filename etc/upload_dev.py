import sys

from requests import post

resp = post('http://localhost/api/plugins', files={
	'file': open(sys.argv[1], 'rb')
})

print(resp)
