# canvas.controllers

## Classes
### APIEndpoint(Controller)
The canonical API endpoint controller base class enforces
a `api/` route prefix and the presence of a description
to allow intuative endpoint presentation.
#### Methods
{mthd_doc_str}
### APIRouteDefinitionError(Exception)
Raised when the route of an `APIEndpointController`
isn't prefixed with `api/`
### Component(object)
The base component class enforces name and targeted 
controller list presence.
#### Methods
{mthd_doc_str}
### ComponentNotFound(HTTPException)
Indicates the component to which the request
was addressed doesn't exist
### Controller(object)
The base controller class enforces route presence
and component management.
#### Methods
{mthd_doc_str}
### NotFound(HTTPException)
Indicates the requested route is unmapped.
Canonically, should never be raised unless
you're abstracting routes
### Page(Controller)
The base page class implements template rendering
for GET requests, dependency management, and supporting
features.
#### Methods
{mthd_doc_str}
### PageComponent(Component)
The base page component class implements template 
rendering and dependency management.
#### Methods
{mthd_doc_str}
### UnsupportedMethod(HTTPException)
Indicates the requested route does not support
the request method. Should not be raised unless
you're abstracting routes
### WrappedDict(dict)
A dictionary with a configurable key error.
#### Methods
{mthd_doc_str}

## Functions
### call_registered(typ)

Invoke all functions registered as `typ`. The 
callback prefix is preppended if not present.
### create_everything()

Create the singleton instance of all controllers and 
components, then add components to controllers.
### get_controller(route_or_controller)
+ *route_or_controller*:  A controller instance or existing route.
Return the controller for the given route or
the parameter if it's already a controller.


### get_controllers(filter)
+ *filter*:  A filter function on controller inclusion.
Return the list of all controller instances.


### get_registered()

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
### render_template(template_path, minify, template_params, response, status, headers)
+ *template_path*:  The path of the template to render, below `/templates`. 
+ *minify*:  Whether or not to minify the template as HTML. By default will only minify .html files. 
+ *template_params*:  An optional dictionary of global variables for the render context. 
+ *response*:  Whether to return a response tuple. 
+ *status*:  The status code for the response, if `response` is true. 
+ *headers*:  The header dictionary for the response, if `response` is true.
Render a Jinja2 template.


