from distutils.core import setup, Extension

module = Extension('numextension',
                    sources = ['numextension.c'])

setup (name = 'NumExtension',
       version = '1.0',
       description = 'Extensions to numpy',
       ext_modules = [module])

