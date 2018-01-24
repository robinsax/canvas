# canvas.controllers

## Classes
### APIEndpoint(Controller)
The canonical API endpoint controller base class enforces
a `api/` route prefix and the presence of a description
to allow intuative endpoint presentation.
#### Methods
#### \_\_init__(self, route, description=No description available)
+ *route*:  The route for this controller, relative to domain root. Must begin with `'/api/'`. 
+ *description*:  A human readable description of the endpoint in markdown. 
+ *super_kwargs*:  The `Controller` class constructors keyword arguments.

Configure the overriding controller class.



#### get(self, ctx)


The GET request method handler.

By default raises an exception that causes
a 405 response code to be returned to the 
client.

#### get_components(self, ctx)


Return all components that that didnt raise an 
exception when their `check()` method was called 
with the current request context.

#### post(self, ctx)


The POST request method handler.

By default raises an exception that causes
a 405 response code to be returned to the 
client.

### APIRouteDefinitionError(Exception)
Raised when the route of an `APIEndpointController`
isn't prefixed with `api/`
### Component(object)
The base component class enforces name and targeted 
controller list presence.
#### Methods
#### \_\_init__(self, name, controllers)
+ *name*:  A unique name for the component used for its identification. 
+ *controllers*:  A list of controller routes to which this component should be added.

Configure the overriding component.



#### check(self, ctx)


Check a request context and raise a subclass of `HTTPException` 
if this component does not want to be available for the 
handling of that request.

Relying on an exception raise allows an informative error 
to be supplied to the client for requests where this component is 
addressed.

By default will never raise an exception.

#### handle_get(self, ctx)


Handle a GET request addressed to this component.

#### handle_post(self, ctx)


Handle a POST request addressed to this component.

### ComponentNotFound(HTTPException)
Indicates the component to which the request
was addressed doesn't exist
### Controller(object)
The base controller class enforces route presence
and component management.
#### Methods
#### \_\_init__(self, route, grab_components=[], block_components=[])
+ *route*:  The route for this controller, relative to domain root. 
+ *grab_components*:  The list of components to add to this controller. Components that are targeting this controller do not need to be specified. 
+ *block_components*:  The list of components that are targeting this controller but should not be added to it.

Configure the overriding controller class.



#### get(self, ctx)


The GET request method handler.

By default raises an exception that causes
a 405 response code to be returned to the 
client.

#### get_components(self, ctx)


Return all components that that didnt raise an 
exception when their `check()` method was called 
with the current request context.

#### post(self, ctx)


The POST request method handler.

By default raises an exception that causes
a 405 response code to be returned to the 
client.

### NotFound(HTTPException)
Indicates the requested route is unmapped.
Canonically, should never be raised unless
you're abstracting routes
### Page(Controller)
The base page class implements template rendering
for GET requests, dependency management, and supporting
features.
#### Methods
#### \_\_init__(self, route, name, dependencies=[], library_dependencies=[], template=None, template_params={}, description=Fast, customizable websites and web applications)
+ *route*:  The route for this controller, relative to domain root. 
+ *name*:  The name of the page with which to populate the title tag. 
+ *template*:  The name of this pages template file, without the `pages/` prefix and `html` file extension. 
+ *dependencies*:  A list of non-library client dependencies. 
+ *library_dependencies*:  A list of library client dependencies. 
+ *template_params*:  A dictionary of additional parameters for this pages template render context. Lambda values will be invoked at render time with a single parameter; the request context. 
+ *super_kwargs*:  The `Controller` class constructors keyword arguments.

Configure the overriding controller class.



#### collect_dependencies(self)


Return a tuple containing respectively the non-library
and library client dependencies of this page, given the 
current request context.

#### get(self, ctx)


Return a response tuple containing the rendered 
template for this page.

#### get_components(self, ctx)


Return all components that that didnt raise an 
exception when their `check()` method was called 
with the current request context.

#### post(self, ctx)


The POST request method handler.

By default raises an exception that causes
a 405 response code to be returned to the 
client.

#### render_component(self, name)


Render the component with name `name` and return its 
rendered template as markup, or return `None` if the
there is no component called `name` available to the
current request context.

#### render_components(self)


Render each component available given the current 
request context and return the sum of their rendered 
templates as markup.

### PageComponent(Component)
The base page component class implements template 
rendering and dependency management.
#### Methods
#### \_\_init__(self, name, pages, template=None, dependencies=[], library_dependencies=[])
+ *name*:  A unique name for the component used for its identification. 
+ *controllers*:  A list of controller routes to which this component should be added. 
+ *template*:  The name of this component's template file, without the `components/` prefix and `html` file extension. 
+ *dependencies*:  A list of non-library client dependencies. 
+ *library_dependencies*:  A list of library client dependencies. 
+ *super_kwargs*:  The `Component` class constructors keyword arguments.

Configure the overriding component.



#### check(self, ctx)


Check a request context and raise a subclass of `HTTPException` 
if this component does not want to be available for the 
handling of that request.

Relying on an exception raise allows an informative error 
to be supplied to the client for requests where this component is 
addressed.

By default will never raise an exception.

#### handle_get(self, ctx)


Handle a GET request addressed to this component.

#### handle_post(self, ctx)


Handle a POST request addressed to this component.

#### render(self, ctx)


Return the rendered template for this component.

### UnsupportedMethod(HTTPException)
Indicates the requested route does not support
the request method. Should not be raised unless
you're abstracting routes
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
### call_registered(typ, *args)


Invoke all functions registered as `typ`. The 
callback prefix is preppended if not present.
### create_everything()


Create the singleton instance of all controllers and 
components, then add components to controllers.
### get_controller(route_or_controller)
+ *route_or_controller*:  A controller instance or existing route.

Return the controller for the given route or
the parameter if it's already a controller.


### get_controllers(filter=<function <lambda> at 0x000002429A7D77B8>)
+ *filter*:  A filter function on controller inclusion.

Return the list of all controller instances.


### get_registered(*types)


Return all registered classes or functions 
registered as the given types or an empty list 
if there are none.
### get_thread_context()


Retrieve the per-thread request context for 
the current thread, or `None` if there
isn't one.
### markup(text)


Transform the string `text` into markup that is 
not escaped when rendered in a template.

Available as a template filter.

__Note__: Beware of XSS vulerabilities when using.
### render_template(template_path, minify=None, template_params={}, response=False, status=200, headers={})
+ *template_path*:  The path of the template to render, below `/templates`. 
+ *minify*:  Whether or not to minify the template as HTML. By default will only minify .html files. 
+ *template_params*:  An optional dictionary of global variables for the render context. 
+ *response*:  Whether to return a response tuple. 
+ *status*:  The status code for the response, if `response` is true. 
+ *headers*:  The header dictionary for the response, if `response` is true.

Render a Jinja2 template.

