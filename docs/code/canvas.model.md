# canvas.model

ORM class, decorator, and utility definitions. 


## Classes
### Session(object)
The `Session` object manages database interaction and relational mapping.
#### Methods
#### \_\_del__(self)

A deconstructor to ensure no database connections
are orphaned.

#### close(self)

Close the underlying database connection for this
session.

#### commit(self)

Write all actively mapped model instances into their 
rows and commit the transaction.

#### delete(self, model)

Delete the row mapped to a loaded model.

#### execute(self, sql, values=())

Execute SQL with debug logging, raising a `ValidationErrors` when an 
integrity check fails.

#### query(self, target, conditions=True, one=False, order_by=None, descending=False)
+ *target*:  The model class (must have been decorated with `model.schema()`). 
+ *conditions*:  A query condition. 
+ *one*:  Whether to return the first result only, or `None` if there are not results.

Query the table mapped to or including `target`, returning mapped 
models if `target` is a model class, scalar values if the it was a
single column, and tuples if it was a tuple of columns


#### reset(self)

Rollback this session, then remove all active mappings.

#### rollback(self)

Undo all changes made during the current transaction.

__TODO__: Rollback changes to model instances too.

#### save(self, model)

Insert a new table row given a constructed model object.

### Column(SQLExpression)
The class-level representation of a table column, placed as a class 
attribute by the `model.schema()` decorator.

Stores type information and generates an SQL-serializable expression 
on comparison.
#### Methods
#### \_\_init__(self, type_str, constraints=[], default=<object object at 0x0000000003478750>, primary_key=False)
+ *type_str*:  A string representation of the column type. 
+ *default*:  The default value to populate this column with. Default values are populated after row insertion since they may be resolved within Postgres. 
+ *primary_key*:  Whether or not this column is the table's primary key.

Create a new column.


#### as_condition(self, values)

Return this expression serialized as an SQL query condition.

#### count(self)

Return the COUNT of this column when queried.

#### get_default(self)

Return the default value for this column, resolving it if it's 
callable.

#### is_max(self)

Return a query condition that this column is maximal.

#### is_min(self)

Return a query condition that this column is minimal.

#### resolve(self, model)

Resolve this column, including its type and constraints.

#### serialize(self, values)

Return an SQL-serialized reference to this column.

#### serialize_node(self, node, values)

A helper function for expression node serialization.

Invoke `serialize()` on `SQLExpression`s and serialize leaves 
(primitive values).

#### set_value_for(self, model_obj, value)

Set the value of this column on the given model 
object.

#### value_for(self, model_obj)

Return the value of this column for the given 
model object.

### Constraint(object)
Base constraint class enforces a name, error message and placeholder 
evaluation methods.
#### Methods
#### \_\_init__(self, name_postfix, error_message)
+ *name_postfix*:  A unique name postfix for the overriding constraint type. 
+ *error_message*:  A human-readable error message to provide when this constraint is violated.

Define a new constraint type.


#### as_client_parsable(self)

Return a client-parsable representation of this constraint for 
client-side validation.

The representation should be of the format `type_name:representation`.

A front-end validation method must then exist for `type_name`.

#### as_sql(self)

Return an SQL serialization of this constraint.

#### check(self, model, value)
+ *model*:  The model object to which the check applies. 
+ *value*:  The value to check, for convience.

Return whether or not the constraint is met by the given input, or 
raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation as 
opposed to the one-at-a-time validation of Postgres.


#### check_with_throw(self, model, value)

Call `check()` and raise a `ValidationErrors` if the check fails. Will 
raise an `UnsupportedEnforcementMethod` if `check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure response to be 
sent to the client.

#### resolve(self, column)

Resolve this constraint as belonging to `Column`.

### RegexConstraint(Constraint)
A regular expression constraint on textual columns.
#### Methods
#### \_\_init__(self, error_message, regex, ignore_case=False, negative=False)
+ *error_message*:  A human-readable error message to provide when this constraint is violated. 
+ *regex*:  The regular expression which the column values must match. 
+ *ignore_case*:  Whether the regular expression should be case-insensitive. 
+ *negative*:  Whether this constraint enforces the column value does *not* match `regex`.

Create a new regular expression constraint.


#### as_client_parsable(self)

Return a client parsable representation of this regular expression 
constraint.

#### as_sql(self)

Return an SQL representation of this regular expression constraint.

#### check(self, model, value)

Evaluate whether `value` satisfies this regular expression constraint.

#### check_with_throw(self, model, value)

Call `check()` and raise a `ValidationErrors` if the check fails. Will 
raise an `UnsupportedEnforcementMethod` if `check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure response to be 
sent to the client.

#### resolve(self, column)

Resolve this constraint as belonging to `Column`.

### UniquenessConstraint(Constraint)
A constraint that enforces column value uniqueness.
#### Methods
#### as_client_parsable(self)

Return a client-parsable representation of this constraint for 
client-side validation.

The representation should be of the format `type_name:representation`.

A front-end validation method must then exist for `type_name`.

#### check(self, model, value)
+ *model*:  The model object to which the check applies. 
+ *value*:  The value to check, for convience.

Return whether or not the constraint is met by the given input, or 
raise an `UnsupportedEnforcementMethod`.

Implementing this method allows a single catch-all validation as 
opposed to the one-at-a-time validation of Postgres.


#### check_with_throw(self, model, value)

Call `check()` and raise a `ValidationErrors` if the check fails. Will 
raise an `UnsupportedEnforcementMethod` if `check()` is not implemented.

Note a `ValidationErrors` will cause a canonical failure response to be 
sent to the client.

#### resolve(self, column)

Resolve this constraint as belonging to `Column`.

### ColumnType(object)
`ColumnType`s are attributes of `Column`s that store information about the
SQL representation of the type.
#### Methods
#### \_\_init__(self, sql_type, input_type=text, default=<object object at 0x0000000003478750>)
+ *sql_type*:  The name of this type in PostgreSQL. 
+ *input_type*:  The type of input to use for this column type if HTML forms. 
+ *default*:  The default value with which to populate attributes in this column.

Define a new column type.


#### resolve(self, owner_column)

Resolve this column type given the owner column.

### ForeignKeyColumnType(ColumnType)
A foreign key column type with target column reference.
#### Methods
#### \_\_init__(self, reference_str)

Create a new foreign key column type referencing the table and column 
specified in `reference_str`.

#### resolve(self, owner_column)

Mixin a `reference` attribute to `owner_column` referencing the target
column.

### EnumColumnType(ColumnType)
An enumerable type column type.
#### Methods
#### \_\_init__(self, enum_name)
+ *enum_name*:  The name of an enumerable type decorated with `@model.enum`.

Create a enum column type targeting the enum 
registered as `enum_name`.


#### resolve(self, owner_column)

Resolve this column type given the owner column.

### TypeAdapter(object)
The base type adaption class.

A psycopg2 type adapter with a casting classmethod.
#### Methods
#### \_\_init__(self, type_name, oid, *types)

Declare the types adapted by the inheriting `TypeAdapter`.

#### adapt(self, obj)

Return `obj` adapted to bytes.

#### cast(self, value)

Return `value` cast to one of the adapted types.

#### existing_adaption(self, obj)

Helper method. Return `obj` adapted and quoted by an existing means.

### SQLExpression(object)
A base class used for object that represent an expression that serializes
to an SQL prepared statement.

Used primarily for query generation.
#### Methods
#### as_condition(self, values)

Return this expression serialized as an SQL query condition.

#### serialize(self, values)
+ *values*:  The current list of values for insertion into the generated prepared statement. Since the expression evaluation is in-order, values should be appended to the `values` list.

The method to implement. Create an SQL representation of the expression.


#### serialize_node(self, node, values)

A helper function for expression node serialization.

Invoke `serialize()` on `SQLExpression`s and serialize leaves 
(primitive values).

### SQLComparison(SQLExpression)
An SQL-serializable expression of model attribute comparison.

Generated by columns on comparison.
#### Methods
#### \_\_and__(self, other)

Return a conjunction of this expression and another.

#### \_\_init__(self, left, right, operator)

Create a column comparator representing a comparsion of `left` to `right` 
using the SQL operator `operator`.

#### \_\_invert__(self)

Group and logically invert this comparison expression.

#### \_\_or__(self, other)

Return a disjunction of this expression and another.

#### as_condition(self, values)

Return this expression serialized as an SQL query condition.

#### group(self)

Group this comparison expression to give it precedence.

#### serialize(self, values)

Serialize this comparison as SQL.

#### serialize_node(self, node, values)

A helper function for expression node serialization.

Invoke `serialize()` on `SQLExpression`s and serialize leaves 
(primitive values).

### SQLAggregatorCall(SQLExpression)
An SQL aggregator function call expression.
#### Methods
#### serialize_node(self, node, values)

A helper function for expression node serialization.

Invoke `serialize()` on `SQLExpression`s and serialize leaves 
(primitive values).


## Functions
### schema(table_name, schema, accessors=None)
+ *table_name*:  The name of the SQL table for this model class. 
+ *schema*:  A column name to column definition mapping. 
+ *accessors*:  A list of column names which are checked for equality by the `get(reference, session)` classmethod.

The model class mapping and schema declaration decorator.

Decorated classes will be added to this package's namespace after 
pre-initialization.

### enum(name)
+ *name*:  A unique name for the enumerable type declaration in Postgres.

The enumerable type model declaration decorator.

Decorated enums will be added to this package's namespace after 
pre-initialization.

### adapter(cls)

A decorator for `TypeAdapter` actualization.
### create_session()

Create a database session. `Session` generation should always use this 
function to allow future modifications to the `Session` constructor.
### create_everything()

Resolve foreign keys and enum references then issue table and enumarable 
type creation SQL.
### dictize(model_obj, omit=[])
+ *model_obj*:  The model class instance to dictize. 
+ *omit*:  A list of columns not to include in the returned dictionary.

Return a dictionary containing a column name, column value mapping for 
`model_obj`.

### dictize_all(model_list, omit=[])
+ *model_list*:  A list of model class instances to dictize. 
+ *omit*:  A list of columns not to include in the returned dictionaries.

Return a list containing dictizations of all the model objects in 
`model_list`.

