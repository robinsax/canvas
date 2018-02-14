# canvas.controllers

`Controller` base class definitions and namespace generation.


## Classes
### Controller(object)
`Controller`s are singleton request handlers attached to a specific route.
They have instance methods for each of the (supported) request methods, 
which are passed a sole parameter; the request context.

The request context is a dictionary containing the request parameters 
and headers (`request`, `headers`), a database session (`session`), and the
cookie session (`cookie`) as a dictionary.

Plugins can extend the request context with the `context_created` callback.
#### Methods
#### \_\_init__(self, route)
+ *route*:  The route for this controller, relative to domain root.

Configure the overriding controller class.


#### get(self, ctx)

The GET request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

#### post(self, ctx)

The POST request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

### Page(Controller)
`Page`s are web page `Controller`s, which serve HTML pages when sent a GET
request.

The `Page` class implements Jinja template ownership rendering as well as 
metadata and dependency management.

*Note*: All `Page` templates should be rendered while by calling 
`super().get()`, as it provides parameters required by the base template.
#### Methods
#### \_\_init__(self, route, title, dependencies=[], library_dependencies=[], template=None, template_params={}, description=Fast, customizable websites and web applications)
+ *route*:  The route for this controller, relative to domain root. 
+ *title*:  The title with which to populate the title tag. 
+ *template*:  The title of this `Page`s' template file, without the `pages/` prefix. 
+ *dependencies*:  A list of non-library client dependencies. 
+ *library_dependencies*:  A list of library client dependencies. 
+ *template_params*:  A dictionary of additional parameters for this `Page`s template rendering context. Lambda values will be invoked at render time with a single parameter; the request context. 
+ *description*:  The content of the `description` field for this `Page`.

Configure the overriding controller class.


#### get(self, ctx)

Return a response tuple containing this `Page`s rendered template.

#### post(self, ctx)

The POST request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

### APIEndpoint(Controller)
`APIEndpoint`s are canonical endpoint `Controller`s that enforce an `api/` 
route prefix.
#### Methods
#### \_\_init__(self, route, description=)
+ *route*:  The route for this controller, relative to domain root. Must begin with `'/api/'`. 
+ *description*:  A human readable description of the endpoint (in Markdown).

Configure the overriding controller class.


#### get(self, ctx)

The GET request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

#### post(self, ctx)

The POST request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

### Redirector(Controller)
A controller that redirects all requests to another URL.

## Functions
### create_everything()

Create the singleton instance of all controllers.
### get_controller(route)

Return the controller for the given route.
