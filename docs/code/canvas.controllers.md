# canvas.controllers

## Classes
### APIEndpoint(Controller)
The canonical API endpoint controller base class enforces
a `api/` route prefix and the presence of a description
to allow intuative endpoint presentation.
#### Methods
### __init__

### get

### get_components

### post


### APIRouteDefinitionError(Exception)
Raised when the route of an `APIEndpointController`
isn't prefixed with `api/`
#### Methods

### Component(object)
The base component class enforces name and targeted 
controller list presence.
#### Methods
### __init__

### check

### handle_get

### handle_post


### ComponentNotFound(HTTPException)
Indicates the component to which the request
was addressed doesn't exist
#### Methods
### __init__


### Controller(object)
The base controller class enforces route presence
and component management.
#### Methods
### __init__

### get

### get_components

### post


### NotFound(HTTPException)
Indicates the requested route is unmapped.
Canonically, should never be raised unless
you're abstracting routes
#### Methods
### __init__


### Page(Controller)
The base page class implements template rendering
for GET requests, dependency management, and supporting
features.
#### Methods
### __init__

### collect_dependencies

### get

### get_components

### post

### render_component

### render_components


### PageComponent(Component)
The base page component class implements template 
rendering and dependency management.
#### Methods
### __init__

### check

### handle_get

### handle_post

### render


### UnsupportedMethod(HTTPException)
Indicates the requested route does not support
the request method. Should not be raised unless
you're abstracting routes
#### Methods
### __init__


### WrappedDict(dict)
A dictionary with a configurable key error.
#### Methods
### __getitem__

### __init__



## Functions
### call_registered
### create_everything
### get_controller
### get_controllers
### get_registered
### get_thread_context
### markup
### render_template
