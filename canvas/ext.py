# coding: utf-8
'''
A namespace module providing access to lower-level canvas functionality.
'''

from .utils import create_callback_registrar, format_exception
from .dictionaries import AttributedDict, RequestParameters, Configuration
from .json_io import json_deserializer, json_serializer
from .core import View, PageView, ErrorView, Controller, Endpoint, Page, \
	RequestContext, RouteVariable, RouteString, Palette, Asset, TypeAdapter, \
	ColumnType, BasicColumnType, Model, Table, plugin_base_path, \
	load_plugins, get_path_occurrences, request_body_parser, resolve_route, \
	directive, transpile_jsx, compile_less, get_palette, get_asset, \
	type_adapter, update_column_types, routing_diag, \
	_loaded_plugins as plugin_list, _sentinel
