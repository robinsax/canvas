# canvas

## Classes
### BuildDocsMode(LaunchMode)
The code documentation generation mode, invoked with '--build_docs'.
### ColumnDefinitionError(Exception)
Raised when an invalid column type is specified
### ComponentNotFound(HTTPException)
Indicates the component to which the request
was addressed doesn't exist
### ConfigKeyError(KeyError)
Raised as the `KeyError` for `config`.
### DevServeMode(LaunchMode)
The development serving mode, invoked with `--serve`.
### HTTPException(Exception)
Represents errors with specific HTTP codes
(e.g. `500`, `404`, etc.)
### LaunchMode(object)
`LaunchMode`s handle command-line
invocation of canvas for a specific mode.
The mode is prefixed with `--` in the command line.

Implementations' constructors must take no
parameters.
#### Methods
#### \_\_init__(self, mode, arg_fmt=)
+ *mode*:  The mode string (e.g. `serve` to be triggered by `--serve`). 
+ *arg_fmt*:  The usage format (i.e. argument specification), as a string

Create a new launch handler. Must be
registered as `launch_mode` for actuation.


#### launch(self, args)
+ *args*:  The command line arguments

Handle a command line invocation. Return `True` if the
command line input was valid and `False` otherwise.

If `False` is returned, the argument specification is
presented.



### MacroParameterError(Exception)
Raised by Jinja macros when they are supplied an invalid
set of parameters
### MarkdownNotFound(Exception)
Raised when a markdown file isn't found
### NotFound(HTTPException)
Indicates the requested route is unmapped.
Canonically, should never be raised unless
you're abstracting routes
### RequestParamError(HTTPException)
Indicates missing request parameters.
Automatically returned as the `KeyError`
replacement for `request` in `vars`
### UnitTestMode(LaunchMode)
The unit test execution mode, invoked with `--run_tests`.
### UnknownAction(HTTPException)
Indicated the action specified by the
client is unknown to the dispatched
controller
### UnsupportedMethod(HTTPException)
Indicates the requested route does not support
the request method. Should not be raised unless
you're abstracting routes
### ValidationErrors(Exception)
Raised when model constraints are violated
by input.
### WrappedDict(dict)
A dictionary with a configurable key error.
#### Methods
#### \_\_getitem__(self, key)


Retrieve the value for `key` or raise
an exception if it's not present.

#### \_\_init__(self, source, exception_cls)
+ *source*:  The dictionary to copy into this dictionary. 
+ *exception_cls*:  The exception class to raise when a missing key is retrieve. Instances will have the offending key passed to their constructor.

Copy the dictionary `source` into this dictionary
and define the exception class to replace `KeyError`.




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
### call_registered(typ, *args)


Invoke all functions registered as `typ`. The 
callback prefix is preppended if not present.
### create_json(status_str, *data, status=200, headers={}, default_serializer=None)
+ *status_str*:  The status string. Should be one of
+ *data*:  (Optional) A data package. 
+ *status*:  The HTTP status code for the response. 
+ *headers*:  A dictionary of headers for the response. 
+ *default_serializer*:  A fallback serialization function for complex objects.

Create a JSON response tuple in the canonical format.

: `'success'`, 
        `'failure'`, or `'error'`.

### export_to_module(module, *items, into_all=True)
+ *module*:  The target module object 
+ *items*:  The functions or classes to place. 
+ *into_all*:  Whether to add the functions or objects to the `__all__` list of the target module.

Export one or more functions or classes onto a module.


### format_traceback(error)
+ *error*:  The raised error.

Return a formatted traceback string for `error` if it has
been raised.


### get_registered(*types)


Return all registered classes or functions 
registered as the given types or an empty list 
if there are none.
### get_registered_by_name(*types)


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
### logger(name=None)
+ *name*:  The name of the logger to create.

Create and return a standard library `logging.Logger`.
When invoked at package level, the name parameter can
be safely omitted.


### markdown(markdown, return_markup=True)
+ *markdown*:  The string to render as markdown. 
+ *return_markup*:  Whether or not to return a markup object that will not be escaped when rendered.

Render a string as markdown.

Available as a template filter.


### markup(text)


Transform the string `text` into markup that is 
not escaped when rendered in a template.

Available as a template filter.

__Note__: Beware of XSS vulerabilities when using.
### place_registered_on(name, typ)
+ *name*:  The name of the module whose namespace is the target. 
+ *typ*:  The registered type to place.

Add all registered classes or functions of the given 
typ to a module or package namespace.

__TODO__(BP): Side-effect: __all__ list modification


### redirect_to(target, code=302)
+ *target*:  The URL to redirect to. 
+ *code*:  The HTTP redirect code. Must be 3xx.

Redirect the view to `target`. Does not return
a value. When called, flow control is halted.

`code` will be ignored if an AJAX POST request
is being handled; The redirection will be formulated
as a view action (it wouldn't work otherwise).


### render_template(template_path, minify=None, template_params={}, response=False, status=200, headers={})
+ *template_path*:  The path of the template to render, below `/templates`. 
+ *minify*:  Whether or not to minify the template as HTML. By default will only minify .html files. 
+ *template_params*:  An optional dictionary of global variables for the render context. 
+ *response*:  Whether to return a response tuple. 
+ *status*:  The status code for the response, if `response` is true. 
+ *headers*:  The header dictionary for the response, if `response` is true.

Render a Jinja2 template.


### uri_encode(s)


Return `s` encoded as a a URI component.
