from setuptools import setup, find_packages

setup(name='ditto',
      version='1.2.2',
      description='Python Class Mocking Framework',
      author='Kyle Derr',
      author_email='kyle.derr@gmail.com',
      url='https://github.com/ironport/ditto',
      packages=find_packages(),
      install_requires=['PyHamcrest'],
      test_suite='ditto.test_ditto',
)
