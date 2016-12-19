from setuptools import setup, find_packages

setup(
    name="social",
    version="0.1",
    license="GPL",
    description="A social media poster",
    author="Greg McCoy",
    author_email="gmccoy4242@gmail.com",
    url="https://github.com/gregmccoy/python-social",
    install_requires=[
        'requests',
        'google-api-python-client',
        'python-docx',
        'termcolor',
    ],
    packages=find_packages(),
)
