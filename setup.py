from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='flickr_download',
      version='0.2.4',
      description='Download a Flickr set',
      long_description=readme(),
      url='https://github.com/beaufour/flickr-download.git',
      author='Allan Beaufour, Marian Such',
      author_email='allan@beaufour.dk, toxygen1@gmail.com',
      license='MIT',
      packages=['flickr_download'],
      install_requires=[
          'flickr_api==0.5',
          'python-dateutil == 1.5',
          'PyYAML==3.11',
      ],
      entry_points={
          'console_scripts': ['flickr_download=flickr_download.flick_download:main'],
      },
      zip_safe=False)
