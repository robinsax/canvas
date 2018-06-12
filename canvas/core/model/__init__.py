# coding: utf-8
'''
This package contains the implementation of canvas's database interaction API.
The large majority of its definition are not exposed as they are not stable 
enough to be extended by plugins.

Note: Within this package's documentation, 'serialize' is equivalent to 
'serialize into SQL'. 
'''

_sentinel = object()

#	TODO: Review this import practice.
from .statements import CreateStatement
from .type_adapters import TypeAdapter, type_adapter
from .model import Model, model
from .tables import Table
from .columns import Column
from .constraints import CheckConstraint, PrimaryKeyConstraint, \
		ForeignKeyConstraint, NotNullConstraint
from .session import Session, create_session

def initialize_model():
	'''
	Finalize the ORM system initialization and create all known in-database 
	objects.
	'''
	#	Create a database session.
	session = create_session()
	
	for table in Table.topo_order():
		#	Bind columns.
		for column in table.columns.values():
			column.bind(table)
		#	Create table.
		session.execute_statement(CreateStatement(table))
	
	session.commit()