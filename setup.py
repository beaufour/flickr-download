from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='flickr_download',
      version='0.1',
      description='Download a Flickr set',
      long_description=readme(),
      url='https://github.com/beaufour/flickr-download.git',
      author='Allan Beaufour',
      author_email='allan@beaufour.dk',
      license='MIT',
      packages=['flickr_download'],
      install_requires=[
          'flickr_api',
          'python-dateutil == 1.5',
      ],
      entry_points={
          'console_scripts': ['flickr_download=flickr_download.flick_download:main'],
      },
      zip_safe=False)
