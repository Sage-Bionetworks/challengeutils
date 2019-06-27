from setuptools import setup, find_packages

setup(
    name='challengeutils',
    version='0.0.1',
    description='Challenge utility functions',
    url='https://github.com/Sage-Bionetworks/challengeutils',
    author='Thomas Yu',
    author_email='thomasyu888@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    python_requires='>=3.5',
    scripts=['bin/runchallenge.py'],
    entry_points={
        'console_scripts': ['challengeutils = challengeutils.__main__:main']},
    install_requires=[
        'pandas>=0.24.1',
        'synapseclient'])
