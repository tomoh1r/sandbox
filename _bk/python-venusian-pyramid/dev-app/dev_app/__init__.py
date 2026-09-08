# coding: utf-8
import venusian
from pyramid.config import Configurator


def main(global_config, **settings):
    import dev_common

    config = Configurator(settings=settings)
    config.include('dev_app')
    config.include('dev_common')
    config.add_route('hello', '/')

    scanner = venusian.Scanner(settings=settings)
    scanner.scan(dev_common)

    return config.make_wsgi_app()


def includeme(config):
    config.include('dev_app.view')
