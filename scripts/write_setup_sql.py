#   coding utf-8
'''
Install script to generate Postgres setup
commands using values from configuration.

Must be invoked from root directory.
'''

import json

with open('./settings.json') as f:
	config = json.load(f)

user = config['user']
database = config['database']
password = config['password']

print(f'''
	CREATE USER {user};
	CREATE DATABASE {database};
	ALTER USER {user} WITH PASSWORD '{password}';
	GRANT * ON DATABASE {database} TO {user};
	\q
''')
