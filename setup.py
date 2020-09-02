import setuptools


def readme():
    with open('README.md') as f:
        return f.read()


setuptools.setup(
    name='perfectextractor',
    version='0.4',
    author='Martijn van der Klis',
    author_email='M.H.vanderKlis@uu.nl',
    description='Extracting Perfects (and related forms) from parallel corpora',
    long_description=readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Text Processing :: Linguistic',
    ],
    url='https://github.com/UUDigitalHumanitieslab/perfectextractor',
    license='MIT',
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'click',
        'lxml',
        'requests',
    ],
)
