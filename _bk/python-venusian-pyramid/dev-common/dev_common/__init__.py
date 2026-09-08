# coding: utf-8
import venusian


def includeme(config):
    from . import dao
    dao.TEST_DATA = config.registry.settings.get('test_data', dao.TEST_DATA)


def set_config(wrapped):
    def callback(scanner, name, ob):
        wrapped(scanner.settings)
    venusian.attach(wrapped, callback)
    return wrapped


@set_config
def env(settings):
    from . import dao
    dao.TEST_DATA2 = settings.get('test_data2', dao.TEST_DATA2)
