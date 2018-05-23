from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='perfectextractor',
      version='0.1',
      description='Extracting present perfects (and related forms) from multilingual corpora',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Text Processing :: Linguistic',
      ],
      url='https://github.com/UUDigitalHumanitieslab/perfectextractor',
      author='Martijn van der Klis',
      author_email='M.H.vanderKlis@uu.nl',
      license='MIT',
      packages=['perfectextractor'],
      install_requires=[
          'lxml',
          'requests',
      ],
      include_package_data=True,
      zip_safe=False)
