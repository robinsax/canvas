# canvas.model

ORM class, decorator, and utility definitions. 


## Classes
### Column(object)
The class-level representation of a table column, placed as
a class attribute by the `model.schema()` decorator.

Stores type information and generates SQL-serializable 
expression on comparison.
#### Methods
#### \_\_init__(self, type_str, constraints=[], default=None, primary_key=False)
+ *type_str*:  A string representation of the column type. 
+ *default*:  The default value to populate this column with. Default values are populated after row insertion since they may be resolved within Postgres. 
+ *primary_key*:  Whether or not this column is the table's primary key.

Create a new column.


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

### Constraint(object)
Base constraint class enforces a name, error message,
and placeholder evaluation methods.
#### Methods
#### \_\_init__(self, name, error_message)
+ *name*:  A unique name for this constraint. 
+ *error_message*:  A human-readable error message to provide when this constraint is violated.

Define a new constraint type.


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
+ *model*:  The model object to which the check applies. 
+ *value*:  The value to check, for convience.

Return whether or not the constraint is met by the
given input, or raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation
as opposed to the one-at-a-time validation of Postgres.


#### check_with_throw(self, model, value)

Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.

### RegexConstraint(Constraint)
A regular expression constraint on textual columns.
#### Methods
#### \_\_init__(self, name, error_message, regex, ignore_case=False, negative=False)
+ *name*:  A unique name for this constraint. 
+ *error_message*:  A human-readable error message to provide when this constraint is violated. 
+ *regex*:  The regular expression which the column values must match. 
+ *ignore_case*:  Whether the regular expression should be case-insensitive. 
+ *negative*:  Whether this constraint enforces the column value does *not* match `regex`.

Create a new regular expression constraint.


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

### UniquenessConstraint(Constraint)
A constraint that enforces column value 
uniqueness.
#### Methods
#### \_\_init__(self, name, error_message)
+ *name*:  A unique name for this constraint. 
+ *error_message*:  A human-readable error message to provide when this constraint is violated.

Define a new constraint type.


#### as_client_parsable(self)

Return a client-parsable representation of this
constraint for client-side validation.

The representation should be of the format 
`type_name:representation`.

A front-end validation method must then exist for 
`type_name`.

#### check(self, model, value)
+ *model*:  The model object to which the check applies. 
+ *value*:  The value to check, for convience.

Return whether or not the constraint is met by the
given input, or raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation
as opposed to the one-at-a-time validation of Postgres.


#### check_with_throw(self, model, value)

Call `check()` and raise a `ValidationErrors` if the check 
fails. Will raise an `UnsupportedEnforcementMethod` if 
`check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure 
response to be sent to the client.

### ColumnType(object)
A column type definition class enforcing and SQL type name,
form input type, and default value.

Column types are transparent to plugins in the majority of
use cases, but can be assumed stable.
#### Methods
#### \_\_init__(self, sql_type, input_type=text, default=<object object at 0x00000210FF7895B0>)
+ *sql_type*:  The name of this type in PostgreSQL. 
+ *input_type*:  The type of input to use for this column type if HTML forms. 
+ *default*:  The default value with which to populate attributes in this column.

Define a new column type.

__TODO__: Extend `input_type` capabilities.


### ForeignKeyColumnType(ColumnType)
A foreign key column type with target column reference.
#### Methods
#### \_\_init__(self, target_name)

Create a new foreign key column type referencing the
table and column specified in `target_name`.

### EnumColumnType(ColumnType)
An enumerable type column type.

__TODO__: Form inputs for this type.
#### Methods
#### \_\_init__(self, enum_name)
+ *enum_name*:  The name of an enumerable type decorated with `@model.enum`.

Create a enum column type targeting the enum 
registered as `enum_name`.



## Functions
### schema(table_name, schema, accessors=[])
+ *table_name*:  The name of the SQL table for this model class. 
+ *schema*:  A column name to column definition mapping. 
+ *accessors*:  A list of column names which are checked for equality by the `get(reference, session)` classmethod.

The model class mapping and schema declaration 
decorator.

Decorated classes will be added to this package's
namespace after pre-initialization.

### enum(name)
+ *name*:  A unique name for the enumerable type declaration in Postgres.

The enumerable type model declaration decorator.

Decorated enums will be added to this package's
namespace after pre-initialization.

### create_session()

Create a database session. `Session` generation should
always use this function to allow future modifications
to the `Session` constructor.
### create_everything()

Resolve foreign keys and enum references then issue table 
and enumarable type creation SQL.
### dictize(model_obj, omit=[])
+ *model_obj*:  The model class instance to dictize. 
+ *omit*:  A list of columns not to include in the returned dictionary.

Return a dictionary containing a column name, column 
value mapping for `model_obj`.

### dictize_all(model_list, omit=[])
+ *model_list*:  A list of model class instances to dictize. 
+ *omit*:  A list of columns not to include in the returned dictionaries.

Return a list containing dictizations of all the model
objects in `model_list`.

