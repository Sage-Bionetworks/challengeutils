"""Setup"""
import os
from setuptools import setup, find_packages

# figure out the version
about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "challengeutils", "__version__.py")) as f:
    exec(f.read(), about)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='challengeutils',
    version=about["__version__"],
    description='Challenge utility functions',
    url='https://github.com/Sage-Bionetworks/challengeutils',
    author='Thomas Yu',
    author_email='thomasyu888@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Apache',
    packages=find_packages(),
    zip_safe=False,
    python_requires='>=3.6, <3.10',
    scripts=['bin/runqueue.py'],
    entry_points={
        'console_scripts': ['challengeutils = challengeutils.__main__:main']
    },
    install_requires=['pandas>=1.1.5',
                      'synapseclient>=2.4.0'],
    project_urls={
        "Documentation": "https://sage-bionetworks.github.io/challengeutils/",
        "Source Code": "https://github.com/Sage-Bionetworks/challengeutils",
        "Bug Tracker": "https://github.com/Sage-Bionetworks/challengeutils/issues",
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics'],
)
