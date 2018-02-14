# canvas

canvas initialization and namespace generation.


## Classes
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


### ValidationErrors(Exception)
An error used to trigger an input validation error response.
### HTTPException(Exception)
An errors with a specific HTTP code (e.g. `500`, `404`, etc.).
### UnsupportedMethod(HTTPException)
An error used internally when an unsupported request method is used.
### BadRequest(HTTPException)
An error triggered by a bad request.
### Unprocessable(HTTPException)
An error triggered by an unprocessable entity.
### RequestParamError(HTTPException)
An error triggered by an incomplete request parameter set.
### UnknownAction(HTTPException)
An error to raise when an invalid `action` parameter is specified in a 
request. 
### NotFound(HTTPException)
An error used internally when an uncontrolled route is requested.
### TemplateNotFound(Exception)
An exception raised when a template cannot be located for render.
### ColumnDefinitionError(Exception)
An error raised when an invalid column type is declared.
### MacroParameterError(Exception)
An exception raised by Jinja macros when they are supplied an invalid set 
of parameters.
### MarkdownNotFound(Exception)
An exception raised when a markdown file doesn't exist.
### PluginConfigError(Exception)
An exception raised if a plugin modifies configuration incorrectly.
### ConfigKeyError(KeyError)
An exception raised as the `KeyError` for `config`.
### HeaderKeyError(KeyError)
An exception raised when a non-present header is retrieved.
### APIRouteDefinitionError(Exception)
An exception raised when the route of an `APIEndpointController` isn't 
prefixed with `api/`.
### TemplateOverlayError(Exception)
An exception raised when the `{% overlay %}` Jinja tag is used in a
bottom-level template.
### UnsupportedEnforcementMethod(Exception)
An exception raised by constraints when an unsupported enforcement
method is invoked.
### InvalidSchema(Exception)
An exception raised when a schema definition is invalid.
### InvalidQuery(Exception)
An exception raised when a `session.query()` is given invalid parameters.
### UnadaptedType(Exception)
An exception raised when an unadaptable leaf is reached in an 
`SQLExpression`.
### Unrecognized(Exception)
An exception raised by `JSONSerializer`s when they are unable to 
deserialize a value.

## Functions
### asset_url(rel_path)

Return the URL relative to domain root for an asset. This method should 
always be called for asset retrieval to allow for forwards-compatability.
### create_json(status_str, *data, status=200, headers={}, fallback_serializer=None)
+ *status_str*:  The status string. Should be one of
+ *data*:  (Optional) A data package. 
+ *status*:  The HTTP status code for the response. 
+ *headers*:  A dictionary of headers for the response. 
+ *fallback_serializer*:  A fallback serialization function for complex objects.

Create a JSON response tuple in the canonical format.

: `'success'`, `'failure'`, 
        or `'error'`.

### redirect_to(target, code=302)
+ *target*:  The URL to redirect to. 
+ *code*:  The HTTP redirect code. Must be `3xx`.

Redirect the view to `target`. Does not return a value. When called, flow 
control is halted.

`code` will be ignored if an AJAX POST request is being handled; The 
redirection will be formulated as a view action (it wouldn't work 
otherwise).

### get_thread_context()

Retrieve the request context mapped to the current thread, or `None` if 
there isn't one.
### flash_message(message)

Flash a message the next time a view or view update is sent.
### render_template(template_path, minify=None, template_params={}, response=False, status=200, headers={})
+ *template_path*:  The path of the template to render relative to `/templates`. 
+ *minify*:  Whether or not to minify the template as HTML. By default will only minify `.html` files. 
+ *template_params*:  An optional dictionary of global variables for the render context. 
+ *response*:  Whether to return a response tuple. 
+ *status*:  The status code for the response, if `response` is `True`. 
+ *headers*:  The header dictionary for the response, if `response` is `True`.

Render a Jinja template.

### format_traceback(error)
+ *error*:  The raised error.

Return a formatted traceback string for `error` if it has
been raised.

### logger(name=None)
+ *name*:  The name of the logger to create.

Create and return a standard library `logging.Logger`.
When invoked at package level, the name parameter can
be safely omitted.

### get_registered(*types)

Return all registered classes or functions registered as the given types 
or an empty list if there are none.
### get_registered_by_name(*types)

Generate and return a dictionary containing all classes or functions 
registered as the given type, keyed by name.
### call_registered(typ, *args)

Invoke all functions registered as `typ`. The callback prefix is 
prepended if not present.
### place_registered_on(name, typ)
+ *name*:  The name of the module whose namespace is the target. 
+ *typ*:  The registered type to place.

Add all registered classes or functions of the given typ to a module or 
package namespace.

### markup(text)

Transform the string `text` into markup that is not escaped when rendered 
in a template.

Beware of XSS vulnerabilities when using. In general, client-sourced data
should always be escaped in templates.
### markdown(markdown, return_markup=True)
+ *markdown*:  The string to render as markdown. 
+ *return_markup*:  Whether or not to return a markup object that will not be escaped when rendered.

Render a string as markdown.

Available as a template filter.

### uri_encode(text)

Return `text` encoded as a a URI component.
### json(obj, camelize_keys=False)
+ *camelize_props*:  Whether to convert snake case keys to camel case.

Return the JSON representation of the JSON-serializable object `obj`.

