# coding: utf-8
'''
Unit tests against the model package, implemented as the creation and usage
of a schema.
'''

import canvas.tests as cvt

from canvas.exceptions import ValidationErrors, Frozen
from canvas.core.model import Column, CheckConstraint, Unique, model, \
	initialize_model, dictized_property, create_session, dictize

#	Define an accessible storage object for models.
test_models = list()

#	Test data.
usa_name = 'United States of America'
china_name = "People's Republic of China"

#	TODO: Fix block when dropping tables on cleanup after error.

@cvt.test('Table definition and creation')
def test_creation():
	#	Create some test models.
	@model('cvt_flags', {
		'id': Column('uuid', primary_key=True),
		'name': Column('text', nullable=False)
	})
	class Flag:

		def __init__(self, name):
			self.name = name

	@model('cvt_countries', {
		'id': Column('uuid', primary_key=True),
		'flag_id': Column('fk:cvt_flags.id'),
		'name': Column('text', unique=True, nullable=False)
	})
	class Country:
		
		def __init__(self, name, flag=None):
			self.name, self.flag_id = name, flag.id if flag else None

		@dictized_property
		def abbreviation(self):
			return ''.join((
				*('.'.join(s[0] for s in self.name.split(' ') if s[0] <= 'Z')),
				'.'
			))

	@model('cvt_companies', {
		'id': Column('uuid', primary_key=True),
		'name': Column('text', nullable=False),
		'country_id': Column('fk:cvt_countries.id', nullable=False),
		'name_copyright': CheckConstraint(
			'That company already exists in that country',
			lambda m: Unique(m.name, m.country_id)
		)
	})
	class Company:

		def __init__(self, name, country):
			self.name, self.country_id = name, country.id

	@model('cvt_employees', {
		'id': Column('uuid', primary_key=True),
		'name': Column('text', nullable=False),
		'religion': Column('text', default='Athiest', dictized=False),
		'garbage': Column('json'),
		'company_id': Column('fk:cvt_companies.id')
	})
	class Employee:

		def __init__(self, name, company, garbage=None):
			self.name = name
			self.company_id, self.garbage = company.id, garbage
	
	session = create_session()
	test_models.extend((Country, Company, Employee, Flag))
	for model_cls in test_models:
		session.execute('DROP TABLE IF EXISTS %s CASCADE;'%model_cls.__table__.name)
	session.commit().close()

	initialize_model()

@cvt.test('Persistance and simple queries')
def test_persistance_and_queries():
	global usa_name
	#	Import the models.
	Country, Company, Employee, Flag = test_models
	#	Create a database session.
	session = create_session()

	#	Create and persist a country.
	china = Country(china_name)
	session.save(china).commit()
	#	Assert success with trivial query.
	with cvt.assertion('Persistance occurs / trivial query case'):
		assert session.query(Country, one=True) is china
	
	with cvt.assertion('Dictization additions included'):
		assert dictize(china)['abbreviation'] == 'P.R.C.'

	#	Try to duplicate.
	with cvt.assertion('Column constraint handling', ValidationErrors):
		session.save(Country(china_name))
	
	session = create_session()
	china_id = china.id
	del china

	#	Create and persist another country, with a flag.
	flag = Flag('Stars and Stripes')
	session.save(flag)
	usa = Country(usa_name, flag)
	session.save(usa).commit()
	usa_id = usa.id
	#	Ensure update occurs.
	usa.name = usa_name = 'United States of Trump'
	session.commit().detach(usa)
	del usa

	usa = Country.get(usa_id, session)
	with cvt.assertion('Update occurs'):
		assert usa.name == usa_name
	
	with cvt.assertion('Conditional and ordered queries'):
		assert (
			(
				session.query(Country, Country.name == china_name, one=True) is
				session.query(Country, order=Country.name.asc)[0]
			) and 
			usa is not session.query(Country, Country.name == china_name, one=True)
		)

	with cvt.assertion('Column queries'):
		names = session.query(Country.name, order=Country.name.asc)
		for name_1, name_2 in zip(names, (china_name, usa_name)):
			assert name_1 == name_2

	with cvt.assertion('Aggregator queries'):
		assert (
			session.query(Country.id.count()) == 2 and
			session.query(Country.id.count(), Country.name == usa_name) == 1 and
			session.query(Country.name.max()) == usa_name
		)
	
	with cvt.assertion('Model classmethod access'):
		china = Country.get(china_id, session)
		assert china.abbreviation == 'P.R.C.'

	#	Create a company.
	ali = Company('Alibaba', china)
	session.save(ali).commit()
	with cvt.assertion('Table level constraints', ValidationErrors):
		session.save(Company('Alibaba', china))
	session.rollback()

	#	Create, query, then purge an employee.
	jack_ma = Employee('Jack Ma', ali, {'is_rich': True})
	session.save(jack_ma).commit()

	with cvt.assertion('Explicit relationship query'):
		assert (
			session.query(Employee, Employee.company_id == ali.id, one=True) is
			jack_ma
		)

	session.detach(jack_ma)
	del jack_ma
	
	#	Test lazy loading. The first case ensures SQL is emitted on access.
	jack_ma = session.query(Employee, one=True)
	session.freeze()
	with cvt.assertion('Lazy loading honoured', Frozen):
		jack_ma.garbage
	#	Fix session.
	session.rollback().unfreeze()

	with cvt.assertion('Lazy loading functional'):
		assert jack_ma.garbage['is_rich'] is True

@cvt.test('Join queries')
def test_join_queries():
	#	Import the models.
	Country, Company, Employee, Flag = test_models
	#	Create a database session.
	session = create_session()

	#	Create more test data.
	china = session.query(Country, Country.name == china_name, one=True)
	alibaba = session.query(Company, Company.name == 'Alibaba', one=True)
	session.save(Company('Tencent', china)).save(Employee('Peng Lei', alibaba)).commit()

	with cvt.assertion('Query execution'):
		data = session.query(
			Country.join(
				Company.join(Employee, attr='employees'), 
				attr='companies'
			).add(Flag, attr='flag')
		)

	#	TODO: Assert contents correct.
