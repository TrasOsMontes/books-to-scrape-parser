'''
' setup.py setup the program and install prerequisites to run the script.
'''
from setuptools import setup
requirements = [r for r in open('requirements.txt', 'r').read().split('\n') if r]

setup(name='Books ToScrape Scraper',
      version='0.1',
      description='Used to scrape the book scraping site and output to the prefered platform.',
      long_description=open('README.md').read(),
      long_description_content_type="text/markdown",
      author='Dom DaFonte',
      author_email='me@domdafonte.com',
      url='https://github.com/TrasOsMontes',
      install_requires=requirements
)