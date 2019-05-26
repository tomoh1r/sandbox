# coding: utf-8
from pyramid.response import Response
from pyramid.view import view_config

from dev_common.dao import get_data


@view_config(route_name='hello')
def hello_world(request):
    return Response(f'<body><h1>Hello World! {get_data()} hoge</h1></body>')
