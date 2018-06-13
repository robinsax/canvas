template = '''
<html>
	<head>
		<title>%s</title>
		<script src="core.js"></script>
		<script src="%s"></script>
	</head>
	<body>
	</body>
</html>
'''

import sys

with open('out.html', 'w') as f:
	f.write(template%tuple(sys.argv[1:]))