#	TODO Critial: No latebind


###

###

###

###

###

###

##


def exec_statement(statement):
	sql, values = statement.write()
	print(sql + ';')
	print(values)


####

####

@model('flags', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'color': Column('text'),
	'metadata': Column('json')
})
class Flag: pass

@model('users', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text', CheckConstraint(lambda x: x < 10)),
	'organization_id': Column('fk:organizations.id')
})
class User: pass

@model('countries', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text'),
	'misc_data': Column('json'),
	'planet_id': Column('fk:planets.id'),
	'flag_id': Column('fk:flags.id')
})
class Country: pass

@model('organizations', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text'),
	'country_id': Column('fk:countries.id')
})
class Organization: pass

@model('planets', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text')
})
class Planet: pass


for t in _tables: #TODO nononononono
	for c in t.columns.values():
		c.type.late_bind(c)

for t in order_tables():
	exec_statement(CreateStatement(t))


#j = planets.join(users.join(orgs).join(countries))
#j = User.join(Organization, Organization.name == 'My Org.').join(Country)
j = Planet.join(Country.join(Organization, Organization.name == 'My Org.', attr='orgs').add(Flag, Flag.color != 'blue'), Planet.name == 'Mars')

exec_statement(SelectStatement(j))
exec_statement(SelectStatement(Country))

c = Country()
c.id = 1
c.__loaded__(True)
c.misc_data
