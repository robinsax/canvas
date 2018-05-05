import canvas as cv
from pprint import pprint
from datetime import datetime

@cv.model('people', {
	'id': cv.Column('uuid', primary_key=True),
	'name': cv.Column('text')
})
class Person:

	def __init__(self, name):
		self.name = name

@cv.model('roles', {
	'id': cv.Column('uuid', primary_key=True),
	'name': cv.Column('text')
})
class Role:

	def __init__(self, name):
		self.name = name

@cv.model('person_roles', {
	'id': cv.Column('uuid', primary_key=True),
	'person_id': cv.Column('fk:people.id'),
	'role_id': cv.Column('fk:roles.id'),
	'started': cv.Column('datetime', default=datetime.now()),
	'ended': cv.Column('datetime', default=None)
})
class PersonRole:

	def __init__(self, person, role):
		self.person_id, self.role_id = person.id, role.id

cv.initialize()

session = cv.create_session()

def create_some():
	jim = Person('Jim')
	session.save(jim).commit()

	dad = Role('Dad')
	drug_addict = Role('Drug Addict')
	session.save(drug_addict, dad).commit()

	jim_as_dad = PersonRole(jim, dad)
	jim_as_drug_addict = PersonRole(jim, drug_addict)
	session.save(jim_as_dad, jim_as_drug_addict).commit()

if False:
	drops = (PersonRole, Person, Role)
	for drop in drops:
		session.execute('drop table %s;'%drop.__table__)
	session.commit()
if False:
	create_some()

now = datetime.now()

from canvas.core.model.sql_factory import selection

def print_result(target, query=True, include=tuple()):
	print(cv.dictize(session.query(target, query), include=include))

print_result(Person.join(PersonRole.onto('role_tags')), include=('role_tags',))
print('--- Nice! ---')
print(Person.join(Role.across(PersonRole).onto('roles')).serialize([]))
print('--- V. Nice! ---')
print(Person.join(Role.across(PersonRole, PersonRole.start <= now).onto('roles')).serialize([]))
print('--- Killmanjaro! ---')

query = Person.join(Role.across(PersonRole, PersonRole.start <= now).onto('roles'))
jim_with_roles = session.query(query, Person.name == 'Jim')

pprint(cv.dictize(jim_with_roles, include=('roles',)))
