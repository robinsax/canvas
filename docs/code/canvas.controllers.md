# canvas.controllers

Controller base class definitions and namespace generation.


## Classes
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

By default raises an exception that causes a `405` response to be 
returned to the client.

#### get_components(self, ctx)

Return all components that that didnt raise an exception when their 
`check()` method was called with the current request context.

#### post(self, ctx)

The POST request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

### Page(Controller)
The base page class implements template rendering for GET requests, 
dependency management, and supporting features.
#### Methods
#### \_\_init__(self, route, title, dependencies=[], library_dependencies=[], template=None, template_params={}, description=Fast, customizable websites and web applications)
+ *route*:  The route for this controller, relative to domain root. 
+ *title*:  The title of the page with which to populate the title tag. 
+ *template*:  The title of this pages template file, without the `pages/` prefix and `html` file extension. 
+ *dependencies*:  A list of non-library client dependencies. 
+ *library_dependencies*:  A list of library client dependencies. 
+ *template_params*:  A dictionary of additional parameters for this pages template render context. Lambda values will be invoked at render time with a single parameter; the request context. 
+ *super_kwargs*:  The `Controller` class constructors keyword arguments.

Configure the overriding controller class.


#### collect_dependencies(self)

Return a tuple containing respectively the non-library and library 
client dependencies of this page, given the current request context.

#### get(self, ctx)

Return a response tuple containing the rendered template for this page.

#### get_components(self, ctx)

Return all components that that didnt raise an exception when their 
`check()` method was called with the current request context.

#### post(self, ctx)

The POST request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

#### render_component(self, name)

Render the component with name `name` and return its rendered template as 
markup, or return `None` if the there is no component called `name` 
available to the current request context.

#### render_components(self)

Render each component available given the current request context and 
return the sum of their rendered templates as markup.

### APIEndpoint(Controller)
The canonical API endpoint controller base class enforces an `api/` route 
prefix and the presence of a description to allow intuative endpoint 
presentation.
#### Methods
#### \_\_init__(self, route, description=No description available)
+ *route*:  The route for this controller, relative to domain root. Must begin with `'/api/'`. 
+ *description*:  A human readable description of the endpoint in markdown. 
+ *super_kwargs*:  The `Controller` class constructors keyword arguments.

Configure the overriding controller class.


#### get(self, ctx)

The GET request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

#### get_components(self, ctx)

Return all components that that didnt raise an exception when their 
`check()` method was called with the current request context.

#### post(self, ctx)

The POST request method handler.

By default raises an exception that causes a `405` response to be 
returned to the client.

### Component(object)
The base component class enforces name and targeted 
controller list presence.
#### Methods
#### \_\_init__(self, name, controllers)
+ *name*:  A unique name for the component used for its identification. 
+ *controllers*:  A list of controller routes to which this component should be added.

Configure the overriding component.


#### check(self, ctx)

Check a request context and raise a subclass of `Unavailable` 
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

Check a request context and raise a subclass of `Unavailable` 
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


## Functions
### create_everything()

Create the singleton instance of all controllers and components, then add 
components to controllers.
### get_controller(route)

Return the controller for the given route.
