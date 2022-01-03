import requests
import lxml.html
import os
import re
import datetime
import unicodedata

from collections import OrderedDict

from bs4 import BeautifulSoup
from bs4.element import (
    CharsetMetaAttributeValue,
    Comment,
    ContentMetaAttributeValue,
    Doctype,
    SoupStrainer
)


def soupedUp(url):
	'''
	' soupedUp:  just makes the request and passes you the soup to parse when there is one available.  Just pass the URL. 
	'''
	theRequest = requests.get(url, allow_redirects=False)
	if theRequest.status_code == 200:
		theRequest.encoding = "utf-8"
		soup = stripTags(theRequest.text, ['br'])
	else:
		soup = None
	return soup

def binarySearch(url, theRange):
	'''
	' binarySearch:  checks through a sequence of numbers to find the last range item in a route.  
	' Helpful when you want to iterate through a sequence of urls to find the last sequence when you don't know it.
	'''
	first = 0
	last = len(theRange)-1
	while first <= last:
		middle = (first + last) // 2
		if soupedUp(url+str(middle)) is None:
			last = middle - 1
		else:
			first = middle + 1
	return middle

def stripTags(html, invalid_tags = ['br']):
	'''
	' stripTags:  Use this to remove the tags that don't add value ie <br>
	'''
	soup = BeautifulSoup(html, 'lxml')
	return soup

def cleanHeader(value):
	'''
	' CleanHeader:  Used to parse out information to be used as a header or field name.
	'''
	if value is not None:
		return value.strip().lower().replace('&', 'and').replace('%', 'pct').replace('-', '_').replace('.','').replace(',', '').replace(":", '').replace('(','').replace(')','').replace('/', '').replace('#', 'number').replace(' ', '_')

def cleanData(value, dataType=None):
	'''
	' cleanData:  Used to clean data into a standard format.
	'''
	if isinstance(value, str) or value is None:	
		if value is None:
			value = ''
		else:
			value = value.strip()
		value = value.replace('"', "'").strip()
	return unicodedata.normalize('NFKD', value).encode('utf8', 'ignore').decode('ascii')

def get_type2(value):
	'''
	' get_type2:  Used to clean data into a standard format.
	'''
	register_type = OrderedDict()

	register_type["INTEGER"] = {"handle":int, "args": [], "kw": {}}
	register_type["DOUBLE"] = {"handle":float, "args": [], "kw": {}}
	register_type["DATE"] = {"handle":lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"), "args": [], "kw": {}}
	register_type["TEXT"] = {"handle":lambda x: re.match("\w+", x), "args": [], "kw": {}}
	
	type_ = "UNKNOWN"
	for k, v in register_type.items():
		try:
			parsed = v["handle"](value, *v["args"], **v["kw"])
			type_ = k
			break
		except ValueError as E:
			continue
	return  type_
