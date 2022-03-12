"""Setup"""
import os
from setuptools import setup

# figure out the version
about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "challengeutils", "__version__.py")) as f:
    exec(f.read(), about)

setup(
    version=about["__version__"]
)
