# coding: utf-8
from .hello import hello_world


def includeme(config):
    config.scan('dev_app.view.hello')
