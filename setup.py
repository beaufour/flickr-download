from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='flickr_download',
      version='0.2.17',
      description='Download photos from Flickr',
      long_description=readme(),
      url='https://github.com/beaufour/flickr-download.git',
      author='Allan Beaufour, Marian Such',
      author_email='allan@beaufour.dk, toxygen1@gmail.com',
      license='Apache',
      packages=['flickr_download'],
      install_requires=[
          'flickr_api==0.5',
          'python-dateutil == 1.5',
          'PyYAML==3.12',
      ],
      test_suite='tests.get_tests',
      tests_require=[
          'unittest2==1.1.0',
          'attrdict==0.5.1',
      ],
      entry_points={
          'console_scripts': ['flickr_download=flickr_download.flick_download:main'],
      },
      zip_safe=False)
