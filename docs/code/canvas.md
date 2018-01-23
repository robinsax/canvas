# canvas

## Classes
### BuildDocsMode(LaunchMode)
The code documentation generation mode, invoked with '--build_docs'.
#### Methods
### __init__

### launch


### ColumnDefinitionError(Exception)
Raised when an invalid column type is specified
#### Methods

### ComponentNotFound(HTTPException)
Indicates the component to which the request
was addressed doesn't exist
#### Methods
### __init__


### ConfigKeyError(KeyError)
Raised as the `KeyError` for `config`.
#### Methods

### DevServeMode(LaunchMode)
The development serving mode, invoked with `--serve`.
#### Methods
### __init__

### launch


### HTTPException(Exception)
Represents errors with specific HTTP codes
(e.g. `500`, `404`, etc.)
#### Methods
### __init__


### LaunchMode(object)
`LaunchMode`s handle command-line
invocation of canvas for a specific mode.
The mode is prefixed with `--` in the command line.

Implementations' constructors must take no
parameters.
#### Methods
### __init__

### launch


### MacroParameterError(Exception)
Raised by Jinja macros when they are supplied an invalid
set of parameters
#### Methods

### MarkdownNotFound(Exception)
Raised when a markdown file isn't found
#### Methods

### NotFound(HTTPException)
Indicates the requested route is unmapped.
Canonically, should never be raised unless
you're abstracting routes
#### Methods
### __init__


### RequestParamError(HTTPException)
Indicates missing request parameters.
Automatically returned as the `KeyError`
replacement for `request` in `vars`
#### Methods
### __init__


### TemplateNotFound(Exception)
*No documentation*
#### Methods

### UnitTestMode(LaunchMode)
The unit test execution mode, invoked with `--run_tests`.
#### Methods
### __init__

### launch


### UnknownAction(HTTPException)
Indicated the action specified by the
client is unknown to the dispatched
controller
#### Methods
### __init__


### UnsupportedMethod(HTTPException)
Indicates the requested route does not support
the request method. Should not be raised unless
you're abstracting routes
#### Methods
### __init__


### ValidationErrors(Exception)
Raised when model constraints are violated
by input.
#### Methods
### __init__


### WrappedDict(dict)
A dictionary with a configurable key error.
#### Methods
### __getitem__

### __init__


### _Redirect(Exception)
*No documentation*
#### Methods
### __init__



## Functions
### handle_request
### asset_url
### call_registered
### create_json
### export_to_module
### format_traceback
### get_registered
### get_registered_by_name
### get_thread_context
### json
### load_all_plugins
### logger
### markdown
### markup
### place_registered_on
### redirect_to
### uri_encode
