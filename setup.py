from setuptools import setup, find_packages

setup(name='refactor',
      version='0.0.1',
      description='Tool(s) to help refactor python code',
      url='http://github.com/dbenamy/refactor',
      author='Daniel Benamy',
      author_email='daniel@benamy.info',
      license='GPLv3',
      packages=find_packages(exclude=['tests']),
      # Deps generated with:
      #   mkvirtualenv venv
      #   pip install redbaron
      #   pip freeze | grep == | grep -v refactor | sort
      install_requires=[
          'appdirs==1.4.3',
          'baron==0.6.6',
          'redbaron==0.6.3',
          'rply==0.7.4',
      ])
