from setuptools import setup, find_packages

# from miniver
def get_version_and_cmdclass(package_path):
    """Load version.py module without importing the whole package.

    Template code from miniver
    """
    import os
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("version", os.path.join(package_path, "_version.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.cmdclass


version, cmdclass = get_version_and_cmdclass("spiro")

setup(name = 'spiro',
      version = version,
      cmdclass = cmdclass,
      packages = find_packages(),
      scripts = ['bin/spiro'],
      install_requires = ['picamera==1.13', 'RPi.GPIO==0.7.0', 'Flask==1.1.1', 'waitress==2.1.1', 'numpy==1.18.1'],
      author = 'Jonas Ohlsson',
      author_email = 'jonas.ohlsson@slu.se',
      description = 'Control software for the SPIRO biological imaging system',
      url = 'https://github.com/jonasoh/spiro',
      include_package_data = True,
      zip_safe = False,
      )
