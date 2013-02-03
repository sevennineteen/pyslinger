from distutils.core import setup

setup(name='Pyslinger',
	version='1.0',
	description='Pythonic Loader for Sling',
	author='Patric DelCioppo',
	author_email='pdelcioppo@gmail.com',
	url='https://github.com/sevennineteen/pyslinger',
	packages=['pyslinger'],
	install_requires=[
		'simplejson',
		'odict',
		'beautifulsoup4',
		]
	)