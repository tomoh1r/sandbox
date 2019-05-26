# coding: utf-8
from setuptools import setup, find_packages


setup(
    name='dev_app',
    install_requires=[
        'pyramid',
        'waitress',
        'pyramid_jinja2',
        'dev_common',
    ],
    packages = find_packages(),
    entry_points="""
    [paste.app_factory]
    main = dev_app:main
    """.strip(),
)
