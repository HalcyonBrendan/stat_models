from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='stat_models',
      version='0.1',
      description='stat_models',
      url='https://github.com/HalcyonBrendan/stat_models',
      author='Brendan Thorn',
      author_email='brendankthorn@gmail.com',
      license='MIT',
      packages=['stat_models'],
      install_requires=[
          'MySQLdb',
          'numpy',
          'pandas'
      ],
      include_package_data=True,
      zip_safe=False)