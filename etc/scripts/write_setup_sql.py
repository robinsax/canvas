#   coding utf-8
'''
Install script to generate Postgres setup commands using values from 
configuration.

Must be invoked from the repository root.
'''

import json

with open('./settings.json') as f:
	database_config = json.load(f)['database']

print('''
	CREATE USER {user};
	CREATE DATABASE {database};
	ALTER USER {user} WITH PASSWORD '{password}';
	GRANT ALL ON DATABASE {database} TO {user};
	\q
'''.format(**database_config))
