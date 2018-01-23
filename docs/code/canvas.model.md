# canvas.model

## Classes
### Column(object)
The class-level representation of a table column, placed as
a class attribute by the `model.schema()` decorator.

Stores type information and generates SQL-serializable 
expression on comparison.
#### Methods
#### \_\_eq__(self, other)
*No documentation*

#### \_\_ge__(self, other)
*No documentation*

#### \_\_gt__(self, other)
*No documentation*

#### \_\_init__(self, type_str, constraints, default, primary_key)
Create a new column.

:type_str A string representation of the column type.
:default The default value to populate this column with. 
        Default values are populated after row insertion since 
        they may be resolved within Postgres.
:primary_key Whether or not this column is the table's
        primary key.

#### \_\_le__(self, other)
*No documentation*

#### \_\_lt__(self, other)
*No documentation*

#### \_\_ne__(self, other)
*No documentation*

#### \_\_repr__(self)
Return a debugging representation. 

#### get_default(self)
Return the default value for this column, resolving
it if it's callable.

#### set_value_for(self, model_obj, value)
Set the value of this column on the given model 
object.

#### value_for(self, model_obj)
Return the value of this column for the given 
model object.


### ColumnDefinitionError(Exception)
Raised when an invalid column type is specified
#### Methods

### ColumnType(object)
A column type definition class enforcing and SQL type name,
form input type, and default value.

Column types are transparent to plugins in the majority of
use cases, but can be assumed stable.
#### Methods
#### \_\_init__(self, sql_type, input_type, default)
Define a new column type.

TODO: Extend `input_type` capabilities.

:sql_type The name of this type in PostgreSQL.
:input_type The type of input to use for this column type
        if HTML forms.
:default The default value with which to populate
        attributes in this column.

#### \_\_repr__(self)
*No documentation*


### Constraint(object)
Base constraint class enforces a name, error message,
and placeholder evaluation methods.
#### Methods
#### \_\_init__(self, name, error_message)
Define a new constraint type.

:name A unique name for this constraint.
:error_message A human-readable error message to 
        provide when this constraint is violated.

#### as_client_parsable(self)
Return a client-parsable representation of this
constraint for client-side validation.

The representation should be of the format 
`type_name:representation`.

A front-end validation method must then exist for 
`type_name`.

#### as_sql(self)
Return an SQL serialization of this constraint.

#### check(self, model, value)
Return whether or not the constraint is met by the
given input, or raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation
as opposed to the one-at-a-time validation of Postgres.

:model The model object to which the check applies.
:value The value to check, for convience.

#### check_with_throw(self, model, value)
Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.


### EnumColumnType(ColumnType)
An enumerable type column type.

TODO: Form inputs for this type.
#### Methods
#### \_\_init__(self, enum_name)
Create a enum column type targeting the enum 
registered as `enum_name`.

:enum_name The name of an enumerable type
        decorated with `@model.enum`.

#### \_\_repr__(self)
*No documentation*


### ForeignKeyColumnType(ColumnType)
A foreign key column type with target column reference.
#### Methods
#### \_\_init__(self, target_name)
Create a new foreign key column type referencing the
table and column specified in `target_name`.

#### \_\_repr__(self)
*No documentation*


### NotNullConstraint(Constraint)
A constraint that enforces non-null column
value.
#### Methods
#### \_\_init__(self, name, error_message)
Define a new constraint type.

:name A unique name for this constraint.
:error_message A human-readable error message to 
        provide when this constraint is violated.

#### as_client_parsable(self)
Return a client-parsable representation of this
constraint for client-side validation.

The representation should be of the format 
`type_name:representation`.

A front-end validation method must then exist for 
`type_name`.

#### as_sql(self)
*No documentation*

#### check(self, model, value)
Return whether or not the constraint is met by the
given input, or raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation
as opposed to the one-at-a-time validation of Postgres.

:model The model object to which the check applies.
:value The value to check, for convience.

#### check_with_throw(self, model, value)
Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.


### RangeConstraint(Constraint)
A range constraint on numerical columns.

TODO: Support all permutation of above and below
        constraint presence on the client side.
#### Methods
#### \_\_init__(self, name, error_message, max_value, min_value)
Create a new regular expression constraint.

:name A unique name for this constraint.
:error_message A human-readable error message to 
        provide when this constraint is violated.
:max_value The maximum value enforced by this constraint.
:min_value The minimum value enforced by this constraint.

#### as_client_parsable(self)
Return a client parsable representation of this 
numerical constraint.

#### as_sql(self)
Return an SQL representation of this numerical
constraint.

#### check(self, model, value)
Return whether or not the constraint is met by the
given input, or raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation
as opposed to the one-at-a-time validation of Postgres.

:model The model object to which the check applies.
:value The value to check, for convience.

#### check_with_throw(self, model, value)
Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.


### RegexConstraint(Constraint)
A regular expression constraint on textual columns.
#### Methods
#### \_\_init__(self, name, error_message, regex, ignore_case, negative)
Create a new regular expression constraint.

:name A unique name for this constraint.
:error_message A human-readable error message to 
        provide when this constraint is violated.
:regex The regular expression which the column values
        must match.
:ignore_case Whether the regular expression should be
        case-insensitive.
:negative Whether this constraint enforces the column
        value does *not* match `regex`.

#### as_client_parsable(self)
Return a client parsable representation of this
regular expression constraint.

#### as_sql(self)
Return an SQL representation of this regular
expression.

#### check(self, model, value)
Evaluate whether `value` satisfies this regular 
expression constraint.

#### check_with_throw(self, model, value)
Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.


### Session(object)
The `Session` object maintains a consecutive set 
of database transactions.
#### Methods
#### \_\_del__(self)
A deconstructor to ensure no database connections
are orphaned.

#### \_\_init__(self)
*No documentation*

#### _load_model(self, model_cls, row)
Map a row to a model. If the row is already mapped
by this session, update the mapping and return the
existing object. Otherwise, create a new instance
and map it.

#### _map_model(self, model, row)
Set values on a model object from a row in the 
corresponding table.

:model The model object to populate with the row 
        values.
:row The row values.

#### _precheck_constraints(self, model)
Check for cumulative constraint violations on a 
model object preceeding a commit, raising a
`ValidationErrors` if any exist and doing nothing
otherwise.

#### _row_reference(self, model)
The canonical row reference format for the 
row reference to model instance mapping.

#### _update_reference(self, model)
Update the stored reference to the row mapped to
`model`.

#### close(self)
Close the underlying database connection for this
session.

#### commit(self)
Write all actively mapped model instances into their 
rows and commit the transaction.

#### delete(self, model)
Delete the row mapped to a loaded model.

#### execute(self, sql, values)
Execute SQL with debug logging, throwing a `ValidationError` 
when an integrity check fails.

#### query(self, model_cls, conditions, one)
Retrieve rows from a table based on some query, then
load them as models and return the resulting model
list.

:model_cls The model class (must have been decorated
        with `model.schema()`).
:conditions A primitive type or comparison on class-level
        column attributes.
:one Whether to return the first result only, or `None`
        if there are not results.

#### rollback(self)
Undo all changes made during the current transaction.

TODO: Rollback changes to model instances too.

#### save(self, model)
Insert a new table row given a constructed model 
object.


### UniquenessConstraint(Constraint)
A constraint that enforces column value 
uniqueness.
#### Methods
#### \_\_init__(self, name, error_message)
Define a new constraint type.

:name A unique name for this constraint.
:error_message A human-readable error message to 
        provide when this constraint is violated.

#### as_client_parsable(self)
Return a client-parsable representation of this
constraint for client-side validation.

The representation should be of the format 
`type_name:representation`.

A front-end validation method must then exist for 
`type_name`.

#### as_sql(self)
*No documentation*

#### check(self, model, value)
Return whether or not the constraint is met by the
given input, or raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation
as opposed to the one-at-a-time validation of Postgres.

:model The model object to which the check applies.
:value The value to check, for convience.

#### check_with_throw(self, model, value)
Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.


### _ColumnIterator(object)
An ordered iterator on the columns of a model class.

The nature of this object is not exposed outside of 
this package.
#### Methods
#### \_\_init__(self, model_cls, yield_i)
Create a column iterator.

:model_cls The mapped model class.
:yield_i Whether the current index should be included 
        in the yielded tuple as a third argument.

#### \_\_iter__(self)
*No documentation*

#### \_\_next__(self)
*No documentation*



## Functions
### create_everything()
Resolve foreign keys and enum references then issue table 
and enumarable type creation SQL.
### create_session()
Create a database session. `Session` generation should
always use this function to allow future modifications
to the `Session` constructor.
### dictize(model_obj, omit)
Return a dictionary containing a column name, column 
value mapping for `model_obj`.

:model_obj The model class instance to dictize.
:omit A list of columns not to include in the returned
        dictionary.
### dictize_all(model_list, omit)
Return a list containing dictizations of all the model
objects in `model_list`.

:model_list A list of model class instances to dictize.
:omit A list of columns not to include in the returned
        dictionaries.
### enum(name)
The enumerable type model declaration decorator.

Decorated enums will be added to this package's
namespace after pre-initialization.

:name A unique name for the enumerable type declaration
        in Postgres.
### enum_creation(enum_cls)
In-Postgres enumerable type creation. Complicated by the 
lack of an IF NOT EXISTS option.
### get_constraint(name)
Return the constraint object with name `name`, or 
`None` if there isn't one.
### schema(table_name, schema, accessors)
The model class mapping and schema declaration 
decorator.

Decorated classes will be added to this package's
namespace after pre-initialization.

:table_name The name of the SQL table for this model 
        class.
:schema A column name to column definition mapping.
:accessors A list of column names which are checked for
        equality by the `get(reference, session)` classmethod.
### table_creation(model_cls)
Serialize a table creation with IF NOT EXISTS option since 
table creation is issued every time canvas is initialized.
