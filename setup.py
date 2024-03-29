import setuptools

from pydeployhelp import __version__

with open('README.md', 'r', encoding='utf-8') as fp:
    long_description = fp.read()

with open('requirements.txt', 'r', encoding='utf-8') as fp:
    requirements = fp.read().splitlines()

setuptools.setup(
    name='pydeployhelp',
    version=__version__,
    author='Ihar Yazerski',
    author_email='ihar.yazerski@outlook.com',
    description='Deploy helper for Python projects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/igorezersky/pydeployhelp',
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'pydeployhelp = pydeployhelp.deploy:run',
            'pydeployhelp-quickstart = pydeployhelp.quickstart:run'
        ]
    },
    python_requires='>=3.6',
)
