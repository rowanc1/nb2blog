from setuptools import setup


setup(
    name='nb2blog',
    version='1.0.0',
    author_email='rowan@3ptscience.com',
    py_modules=['nb2blog'],
    entry_points={
        'console_scripts': [
            'nb2blog = nb2blog:main',
        ],
    },
    install_requires=[
    ],
    classifiers=[
      'Environment :: Console'
    ],
)
