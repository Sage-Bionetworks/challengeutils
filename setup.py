from setuptools import setup, find_packages

setup(name='challengeutils',
      version='0.0.1',
      description='DREAM utility functions',
      url='https://github.com/Sage-Bionetworks/DREAM-Utilities',
      author='Thomas Yu',
      author_email='thomasyu888@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      entry_points = {
        'console_scripts': ['challengeutils = challengeutils.__main__:main']},
      install_requires=[
        'pandas>=0.20.0',
        'synapseclient'])