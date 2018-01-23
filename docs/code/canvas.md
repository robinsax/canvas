# canvas

## Classes
### BuildDocsMode(LaunchMode)
The code documentation generation mode, invoked with '--build_docs'.
#### Methods
#### \_\_init__(self)
*No documentation*

#### launch(self, args)
*No documentation*


### ColumnDefinitionError(Exception)
Raised when an invalid column type is specified
#### Methods

### ComponentNotFound(HTTPException)
Indicates the component to which the request
was addressed doesn't exist
#### Methods
#### \_\_init__(self, component)
*No documentation*


### ConfigKeyError(KeyError)
Raised as the `KeyError` for `config`.
#### Methods

### DevServeMode(LaunchMode)
The development serving mode, invoked with `--serve`.
#### Methods
#### \_\_init__(self)
*No documentation*

#### launch(self, args)
*No documentation*


### HTTPException(Exception)
Represents errors with specific HTTP codes
(e.g. `500`, `404`, etc.)
#### Methods
#### \_\_init__(self, msg, code, desc)
*No documentation*


### LaunchMode(object)
`LaunchMode`s handle command-line
invocation of canvas for a specific mode.
The mode is prefixed with `--` in the command line.

Implementations' constructors must take no
parameters.
#### Methods
#### \_\_init__(self, mode, arg_fmt)
Create a new launch handler. Must be
registered as `launch_mode` for actuation.
:mode The mode string (e.g. `serve` to be triggered
        by `--serve`).
:arg_fmt The usage format (i.e. argument specification),
        as a string

#### launch(self, args)
Handle a command line invocation. Return `True` if the
command line input was valid and `False` otherwise.

If `False` is returned, the argument specification is
presented.

:args The command line arguments


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
#### \_\_init__(self, key)
*No documentation*


### RequestParamError(HTTPException)
Indicates missing request parameters.
Automatically returned as the `KeyError`
replacement for `request` in `vars`
#### Methods
#### \_\_init__(self, param)
*No documentation*


### TemplateNotFound(Exception)
*No documentation*
#### Methods

### UnitTestMode(LaunchMode)
The unit test execution mode, invoked with `--run_tests`.
#### Methods
#### \_\_init__(self)
*No documentation*

#### launch(self, args)
*No documentation*


### UnknownAction(HTTPException)
Indicated the action specified by the
client is unknown to the dispatched
controller
#### Methods
#### \_\_init__(self, action)
*No documentation*


### UnsupportedMethod(HTTPException)
Indicates the requested route does not support
the request method. Should not be raised unless
you're abstracting routes
#### Methods
#### \_\_init__(self)
*No documentation*


### ValidationErrors(Exception)
Raised when model constraints are violated
by input.
#### Methods
#### \_\_init__(self, error_dict)
*No documentation*


### WrappedDict(dict)
A dictionary with a configurable key error.
#### Methods
#### \_\_getitem__(self, key)
Retrieve the value for `key` or raise
an exception if it's not present.

#### \_\_init__(self, source, exception_cls)
Copy the dictionary `source` into this dictionary
and define the exception class to replace `KeyError`.

:source The dictionary to copy into this
        dictionary.
:exception_cls The exception class to raise when
        a missing key is retrieve. Instances will have the
        offending key passed to their constructor.


### _Redirect(Exception)
*No documentation*
#### Methods
#### \_\_init__(self, target, code)
*No documentation*



## Functions
### handle_request(environ, start_response)
The WSGI application, exported to the root package
as `application`.

Invokes either the controller or asset request handler,
expecting them to return a tuple containing:
```
response, status, headers, mimetype
```
### asset_url(rel_path)
Return the URL relative to domain root for an asset. 
This message should always be called for asset 
retrieval to allow for forwards-compatability.
### call_registered(typ)
Invoke all functions registered as `typ`. The 
callback prefix is preppended if not present.
### create_json(status_str, status=200, headers={}, default_serializer=None)
Create a JSON response tuple in the canonical format.

:status_str The status string. Should be one of: `'success'`, 
        `'failure'`, or `'error'`.
:data (Optional) A data package.
:status The HTTP status code for the response.
:headers A dictionary of headers for the response.
:default_serializer A fallback serialization function for 
        complex objects.
### export_to_module(module, into_all=True)
Export one or more functions or classes onto a module.

:module The target module object
:items The functions or classes to place.
:into_all Whether to add the functions or objects
        to the `__all__` list of the target module.
### format_traceback(error)
Return a formatted traceback string for `error` if it has
been raised.

:error The raised error.
### get_registered()
Return all registered classes or functions 
registered as the given types or an empty list 
if there are none.
### get_registered_by_name()
Generate and return a dictionary containing all 
classes or functions registered as the given type, 
keyed by name.
### get_thread_context()
Retrieve the per-thread request context for 
the current thread, or `None` if there
isn't one.
### json(o)
Return the JSON representation of the
JSON-serializable object `o`.
### load_all_plugins()
Initialize all plugins activated in configuration
and populate the `canvas.plugins` namespace.
### logger(name)
Create and return a standard library `logging.Logger`.
When invoked at package level, the name parameter can
be safely omitted.

:name The name of the logger to create.
### markdown(markdown, return_markup)
Render a string as markdown.

Available as a template filter.

:markdown The string to render as markdown.
:return_markup Whether or not to return a markup object
        that will not be escaped when rendered.
### markup(text)
Transform the string `text` into markup that is 
not escaped when rendered in a template.

Available as a template filter.

__Note__: Beware of XSS vulerabilities when using.
### place_registered_on(name, typ)
Add all registered classes or functions of the given 
typ to a module or package namespace.

TODO(BP): Side-effect: __all__ list modification

:name The name of the module whose namespace is
        the target.
:typ The registered type to place.
### redirect_to(target, code)
Redirect the view to `target`. Does not return
a value. When called, flow control is halted.

`code` will be ignored if an AJAX POST request
is being handled; The redirection will be formulated
as a view action (it wouldn't work otherwise).

:target The URL to redirect to.
:code The HTTP redirect code. Must be 3xx.
### uri_encode(s)
Return `s` encoded as a a URI component.
