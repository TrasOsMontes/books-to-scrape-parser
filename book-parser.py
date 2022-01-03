#External Libraries
import json, csv
import os,sys
import logging
import argparse

#internal libraries
sys.path.insert(0, './lib')
from scraperlibrary import (
    soupedUp,
    cleanHeader,
    cleanData,
)
from etllibrary import ETL

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output",
                        type=str,
                        action="store",
                        default=None,
                        help="""options: json, csv, mySQL
                        	Where you would like your parsed data to be stored.  If you want to output to mySQL, make sure you add your mysql credentials and host to the .env file.""")
parser.add_argument("-c", "--categories",
                        type=str,
                        action="append",
                        default=[],
                        help="These are the categories you intend on parsing for.  To receive a list of available ategories, you can pass -cgrep. ")

parser.add_argument("-clist", "--list_categories",
                        action="store_true",
                        help="pass this variable if you need help finding the categories you want to parse.  This argument will print all available categories.")

arg = parser.parse_args()

## Initialize the environment
env = json.load(open('.env'))

##initialize Logging
if not os.path.exists(env['logPath']):
    os.makedirs(env['logPath'])
if not os.path.exists(env['dataPath']):
    os.makedirs(env['dataPath'])

logFile = env['logPath']+env['app']+'.log'
logging.basicConfig(filename=logFile, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
print('This script will be logged in: '+logFile)

def getCategories(url):
	'''
	' getCategories: This function will take in the souped html object and grab the categories from the section.  
	' It then creates a dictionary of categories that we can access to identify which categories of books we want to parse.
	'''
	logging.info('getCategories:: Extracting Categories from sidebar class side_categories.')
	soup = soupedUp(url)
	categories = soup.find('div', class_ = "side_categories" )
	categoryDictionary = dict()
	for category in categories.find_all('a'):
		categoryDictionary.update({cleanHeader(category.text) : cleanData(url+category['href'])})
	return categoryDictionary

def getPages(soup):
	'''
	' getPages: This function takes in the soup formatted html object and finds the section with page details.
	' if the object doesn't exist there should only be one page worth of books.
	'''
	logging.info('getPages:: Checking how many pages we need to scrape from the pager class.')
	pager = soup.find("ul", class_ = "pager" )
	if not pager:
		pages = 1
	else:
		pages = cleanData(pager.find("li", class_ = "current").text).split(" of ")[1]
	return pages

def parseBookDetails(url,category):
	'''
	' parseBookDetails: this function will take in the url to parse book details from and then parse the items
	' we're interested in.  Specifically the product description, the title, image of the book, and the items in product information.
	'''
	bookSoup = soupedUp(url)
	pages = int(getPages(bookSoup))
	logging.info('parseBookDetails:: We have '+str(pages)+' pages of books to parse.')
	productList = []
	for i in range(pages):
		#modify the page in case there is pagination we want to capture 
		#all products on the page html like #page-2.
		pageURL = url.replace('index.html','page-'+str(i+1))+'.html' if pages > 1 else url
		logging.info('parseBookDetails:: Processing '+pageURL+' which is page '+str(i)+'.')
		pageSoup = soupedUp(pageURL)
		
		###Scrape product description and all product info
		books = pageSoup.find_all('article', class_ = "product_pod" )
		for book in books:
			bookDictionary = dict()
			bookURL = env['url']+book.find('a')["href"].replace(' ','').replace('../../..','catalogue')
			logging.info('parseBookDetails:: Processing '+bookURL+' for product information.')
			bookDictionary.update({'url' : bookURL})
			bookDictionary.update({'category' : category})

			#get image and title
			bookImage = soupedUp(bookURL).find("div", id = "product_gallery")
			theImage = bookImage.findNext('img')

			bookDictionary.update({'title' : theImage['alt']})
			bookDictionary.update({'image' : theImage['src'].replace('../../',env['url'])})

			bookDetails = soupedUp(bookURL).find("div", id = "product_description")
			productDescription = bookDetails.findNext('p').text
			bookDictionary.update({'product_description' : productDescription})
			
			productInformation = bookDetails.findNext('table')
			#bookDictionary.update({'date_created':'now()'})
			#bookDictionary.update({'date_updated':'now()'})
			for item in productInformation.find_all('tr'):
				bookDictionary.update({cleanHeader(item.th.string) : item.td.string})
			productList.append(bookDictionary)
			logging.info('parseBookDetails:: '+bookDictionary['title']+' has been parsed.')
	print('parseBookDetails:: Parsed '+str(len(productList))+' books from the category: '+category)
	return productList

def processBooksToDataSource(productList,dataSource='json'):
	'''
	' processBooksToDataSource: will take the data and process it through the available data source methods.  
	' json - Will create a list of json objects in a json file.
	' csv - will create a comma delimited file
	' mySQL - Will create a products table with the data based on your .env database 
	'''	
	if dataSource == 'json':
		data = json.dumps(productList,indent=1,ensure_ascii=False)
		output = env['dataPath']+env['app']+".json"		
		with open(output, "w") as file:
			file.write(data)
	elif dataSource == 'csv':
		data = productList
		output = env['dataPath']+env['app']+'.csv'
		with open(output, 'w') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames = data[0].keys())
			writer.writeheader()
			writer.writerows(data)		
	elif dataSource == 'mySQL':
		db = env['db']
		dbLoad = ETL(env['host'], env['user'], env['pw'], env['db'], logging, env['schemaFile'], env['charset'])
		output = env['host']+'.'+env['db']
		### Create the schema using the schema json file
		dbLoad.createSchema() #This creates the schema based on the json file you created
		for product in productList:
			product = dbLoad.writeTable('products', product)
	print('processBooksToDataSource:: Books Processed to '+dataSource+'. You\'ll find your data in '+output)
	return productList


def main(arg):
	if arg.list_categories:
		print('Here are the categories you can parse for:', ', '.join(sorted(getCategories(env['url']).keys())))
	elif arg.categories and arg.output:
		categoryList = getCategories(env['url'])
		categories = arg.categories

		for i in categories:
			catURL = categoryList[i]
			productList = parseBookDetails(catURL,i)
			processBooksToDataSource(productList,arg.output)
	else:
		print('It looks like you are missing some required parameters.  Please pass the categories you would like to parse and the output type you require.  You can pass --help if you  need some help.')

if __name__ == "__main__":
	main(arg)		