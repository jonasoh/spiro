from setuptools import setup, find_packages
setup(name = 'spiro',
      version = '1.0a1',
      package_dir = {'': 'src'},
      packages = find_packages(where='src'),
      scripts = ['bin/spiro'],
      install_requires = ['picamera==1.13', 'RPi.GPIO==0.6.5'],
      author = 'Jonas Ohlsson',
      author_email = 'jonas.ohlsson@slu.se',
      description = 'Control software for the SPIRO biological imaging system',
      url = 'https://github.com/jonasoh/spiro',
      zip_safe = True,
      )
