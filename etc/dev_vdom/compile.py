import re

_directives = dict()

def directive(name, priority=0):
	def directive_inner(cls):
		cls.__priority__ = priority
		_directives[name] = cls()
		return cls
	return directive_inner

@directive('import', 2)
class ImportDirective:

	def apply(self, target, *args):
		to_import = ', '.join(["'%s'"%i for i in args])
		return 'cv.import([%s], () => {\n%s\n});'%(to_import, target)

@directive('style', 3)
class StyleDirective:

	def apply(self, target, *args):
		styles = ', '.join(["'%s'"%i for i in args])
		return 'cv.loadStyle(%s);\n%s'%(styles, target)

@directive('export', 1)
class ExportDirective:

	def apply(self, target, *args):
		to_export = ',\n'.join(["%s: %s"%(a, a) for a in args])
		return "%s\ncv.export('%s', {\n%s\n});"%(target, self.package_name, to_export)

##############################################
import sys
from subprocess import Popen

filename = sys.argv[1]
with open(filename) as f:
	content = f.read()

directives = list()
regex = r'\/\/\s*::(\w+)\s+(.*)'
ds = []
for one in re.finditer(regex, content):
	args = [a.strip() for a in one.group(2).split(',')]
	ds.append([_directives[one.group(1)], args])	

processed = re.sub(regex, '', content)
for d in sorted(ds, key=lambda x: x[0].__priority__):
	d[0].package_name = sys.argv[2].split('.')[0]
	processed = d[0].apply(processed, *d[1])
processed = '(() => {\n%s\n})();'%processed

tmpfile = '%s.tmp'%filename
with open(tmpfile, 'w') as f:
	f.write(processed)

Popen('node build.js %s %s'%(tmpfile, sys.argv[2]), shell=True).communicate()
