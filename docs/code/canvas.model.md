# canvas.model

## Classes
### Column(object)
The class-level representation of a table column, placed as
a class attribute by the `model.schema()` decorator.

Stores type information and generates SQL-serializable 
expression on comparison.
#### Methods
### __eq__

### __ge__

### __gt__

### __init__

### __le__

### __lt__

### __ne__

### __repr__

### get_default

### set_value_for

### value_for


### ColumnDefinitionError(Exception)
Raised when an invalid column type is specified
#### Methods

### ColumnType(object)
A column type definition class enforcing and SQL type name,
form input type, and default value.

Column types are transparent to plugins in the majority of
use cases, but can be assumed stable.
#### Methods
### __init__

### __repr__


### Constraint(object)
Base constraint class enforces a name, error message,
and placeholder evaluation methods.
#### Methods
### __init__

### as_client_parsable

### as_sql

### check

### check_with_throw


### EnumColumnType(ColumnType)
An enumerable type column type.

TODO: Form inputs for this type.
#### Methods
### __init__

### __repr__


### ForeignKeyColumnType(ColumnType)
A foreign key column type with target column reference.
#### Methods
### __init__

### __repr__


### NotNullConstraint(Constraint)
A constraint that enforces non-null column
value.
#### Methods
### __init__

### as_client_parsable

### as_sql

### check

### check_with_throw


### RangeConstraint(Constraint)
A range constraint on numerical columns.

TODO: Support all permutation of above and below
        constraint presence on the client side.
#### Methods
### __init__

### as_client_parsable

### as_sql

### check

### check_with_throw


### RegexConstraint(Constraint)
A regular expression constraint on textual columns.
#### Methods
### __init__

### as_client_parsable

### as_sql

### check

### check_with_throw


### Session(object)
The `Session` object maintains a consecutive set 
of database transactions.
#### Methods
### __del__

### __init__

### _load_model

### _map_model

### _precheck_constraints

### _row_reference

### _update_reference

### close

### commit

### delete

### execute

### query

### rollback

### save


### UniquenessConstraint(Constraint)
A constraint that enforces column value 
uniqueness.
#### Methods
### __init__

### as_client_parsable

### as_sql

### check

### check_with_throw


### _ColumnIterator(object)
An ordered iterator on the columns of a model class.

The nature of this object is not exposed outside of 
this package.
#### Methods
### __init__

### __iter__

### __next__



## Functions
### create_everything
### create_session
### dictize
### dictize_all
### enum
### enum_creation
### get_constraint
### schema
### table_creation
