from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(name='flickr_download',
      version='0.2.21',
      description='Download photos from Flickr',
      long_description=readme(),
      long_description_content_type='text/markdown',
      url='https://github.com/beaufour/flickr-download.git',
      author='Allan Beaufour',
      author_email='allan@beaufour.dk',
      license='Apache',
      packages=['flickr_download'],
      install_requires=[
          'flickr_api >= 0.7.3',
          'python-dateutil == 2.8.1',
          'PyYAML >= 5.3',
      ],
      test_suite='tests.get_tests',
      tests_require=[
          'attrdict == 2.0.1',
      ],
      entry_points={
          'console_scripts': ['flickr_download=flickr_download.flick_download:main'],
      },
      zip_safe=False)
