from distutils.core import setup

setup(name='Pyslinger',
	version='1.1',
	description='Pythonic Loader for Sling',
	author='Patric DelCioppo',
	author_email='pdelcioppo@gmail.com',
	url='https://github.com/sevennineteen/pyslinger',
	packages=['pyslinger'],
	install_requires=[
                'httplib2',
		'simplejson',
		'odict',
		'beautifulsoup4',
		]
	)
