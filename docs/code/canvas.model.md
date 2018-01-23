# canvas.model

## Classes
### Column(object)
The class-level representation of a table column, placed as
a class attribute by the `model.schema()` decorator.

Stores type information and generates SQL-serializable 
expression on comparison.
#### Methods
{mthd_doc_str}
### ColumnDefinitionError(Exception)
Raised when an invalid column type is specified
### ColumnType(object)
A column type definition class enforcing and SQL type name,
form input type, and default value.

Column types are transparent to plugins in the majority of
use cases, but can be assumed stable.
#### Methods
{mthd_doc_str}
### Constraint(object)
Base constraint class enforces a name, error message,
and placeholder evaluation methods.
#### Methods
{mthd_doc_str}
### EnumColumnType(ColumnType)
An enumerable type column type.

__TODO__: Form inputs for this type.
#### Methods
{mthd_doc_str}
### ForeignKeyColumnType(ColumnType)
A foreign key column type with target column reference.
#### Methods
{mthd_doc_str}
### NotNullConstraint(Constraint)
A constraint that enforces non-null column
value.
#### Methods
{mthd_doc_str}
### RangeConstraint(Constraint)
A range constraint on numerical columns.

__TODO__: Support all permutation of above and below
        constraint presence on the client side.
#### Methods
{mthd_doc_str}
### RegexConstraint(Constraint)
A regular expression constraint on textual columns.
#### Methods
{mthd_doc_str}
### Session(object)
The `Session` object maintains a consecutive set 
of database transactions.
#### Methods
{mthd_doc_str}
### UniquenessConstraint(Constraint)
A constraint that enforces column value 
uniqueness.
#### Methods
{mthd_doc_str}
### _ColumnIterator(object)
An ordered iterator on the columns of a model class.

The nature of this object is not exposed outside of 
this package.
#### Methods
{mthd_doc_str}

## Functions
### create_everything()

Resolve foreign keys and enum references then issue table 
and enumarable type creation SQL.
### create_session()

Create a database session. `Session` generation should
always use this function to allow future modifications
to the `Session` constructor.
### dictize(model_obj, omit)
+ *model_obj*:  The model class instance to dictize. 
+ *omit*:  A list of columns not to include in the returned dictionary.
Return a dictionary containing a column name, column 
value mapping for `model_obj`.


### dictize_all(model_list, omit)
+ *model_list*:  A list of model class instances to dictize. 
+ *omit*:  A list of columns not to include in the returned dictionaries.
Return a list containing dictizations of all the model
objects in `model_list`.


### enum(name)
+ *name*:  A unique name for the enumerable type declaration in Postgres.
The enumerable type model declaration decorator.

Decorated enums will be added to this package's
namespace after pre-initialization.


### enum_creation(enum_cls)

In-Postgres enumerable type creation. Complicated by the 
lack of an IF NOT EXISTS option.
### get_constraint(name)

Return the constraint object with name `name`, or 
`None` if there isn't one.
### schema(table_name, schema, accessors)
+ *table_name*:  The name of the SQL table for this model class. 
+ *schema*:  A column name to column definition mapping. 
+ *accessors*:  A list of column names which are checked for equality by the `get(reference, session)` classmethod.
The model class mapping and schema declaration 
decorator.

Decorated classes will be added to this package's
namespace after pre-initialization.


### table_creation(model_cls)

Serialize a table creation with IF NOT EXISTS option since 
table creation is issued every time canvas is initialized.
