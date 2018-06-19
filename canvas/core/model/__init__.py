# coding: utf-8
'''
This package contains the implementation of canvas's database interaction API.
The large majority of its definition are not exposed as they are not stable 
enough to be extended by plugins.

Note: Within this package's documentation, 'serialize' is equivalent to 
'serialize into SQL'. 
'''

#	Define a sentinel value for determining when model attributes have been
#	populated.
_sentinel = object()

#	TODO: Review this import practice.
from .statements import CreateStatement
from .ast import Unique
from .type_adapters import TypeAdapter, type_adapter
from .model import Model, model
from .tables import Table
from .columns import Column
from .constraints import CheckConstraint, PrimaryKeyConstraint, \
	ForeignKeyConstraint, NotNullConstraint, UniquenessConstraint, \
	RegexConstraint
from .session import Session, create_session
from .dictizations import dictized_property, dictize

def initialize_model():
	'''
	Finalize the ORM system initialization and create all known in-database 
	objects.
	'''
	Table.build_relations()

	#	Create a database session.
	session = create_session()
	
	for table in Table.instances:
		#	Bind columns.
		for column in table.columns.values():
			column.post_bind()
	
	for table in Table.topo_order():
		#	Create table.
		session.execute_statement(CreateStatement(table))
	
	session.commit()
