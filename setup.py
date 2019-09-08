import os
from setuptools import find_packages, setup


with open(
    os.path.join(os.path.dirname(__file__), "djangochaos", "README.rst")
) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="djangochaos",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    license="BSD License",
    description="A Django app to introduce controlled failure into projects.",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://www.gitlab.com/nkuttler/djangochaos/",
    author="Nicolas Kuttler",
    author_email="django@kuttler.eu",
    classifiers=[
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Testing :: Mocking",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.5",
)
