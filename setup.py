import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="scrapy-crawlera-fetch",
    version="0.0.1",
    license="BSD",
    description="Scrapy downloader middleware to interact with Crawlera Simple Fetch API",
    long_description=long_description,
    author="Scrapinghub",
    author_email="info@scrapinghub.com",
    url="https://github.com/scrapy-plugins/scrapy-crawlera-fetch",
    packages=["crawlera_fetch"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Scrapy",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=["scrapy>=1.6.0", "w3lib"],
)
