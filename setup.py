from setuptools import setup

setup(name='stat_models',
      version='0.1',
      description='Package to build NHL statistical models',
      url='http://github.com/storborg/funniest',
      author='Brendan Thorn',
      author_email='brendankthorn@gmail.com',
      license='MIT',
      packages=['stat_models'],
      install_requires=[
          'MySQLdb',
          'numpy',
          'pandas'
      ],
      zip_safe=False)