# coding: utf-8
'''
This package contains the implementation of canvas's database interaction API.

Note: Within this package's documentation, 'serialize' is equivalent to 
'serialize into SQL'. 
'''

_sentinel = object()

from .type_adapters import TypeAdapter, type_adapter
from .model import Model, model
from .columns import Column
from .constraints import CheckConstraint, PrimaryKeyConstraint, \
		ForeignKeyConstraint, NotNullConstraint
