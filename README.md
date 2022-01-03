# Books To Scrape Parser

This program was built to parse the product details for books from http://books.toscrape.com/ based on book category.

## Description

Books To Scrape Parser will allow you to parse books based on their category from the books.toscrape website.  Simply pass the book-parser.py script the categories you'd like to scrape in a list format and the format you'd like the script to output the data and the script will function.  


## Getting Started

### Dependencies

* Python 3.7.10.  The script can work with earlier versions of Python, but the installation process will require manual effort, likely requiring manually installing all the requirements in requirements.txt via pip.

The below list of dependencies will be installed when you run the installation.
* requests is used to request the html from the site to parse and to check whether it is a valid website.  
* Beautiful Soup4 (BS4) coupled with lxml is used to scrape the html 
* If you want to output the data to mysql, PyMysql is used by the ETL class to interact with mysql. Additionally, you will need a functioning MySQL database with access to create databases and tables. 

### Installing

Books ToScrape Parser is written in Python 3. You should install at least Python 3.6. 

To install Books To Scrape Parser you simply clone the project, cd into it, create your virtual environment and install the required external libraries through running the setup file.  Here are step by step installation instructions. 
```
git clone https://github.com/TrasOsMontes/books-to-scrape-parser.git
cd books-to-scrape-parser
python3 -m venv env
source env/bin/activate
python3 setup.py install
```

#### Configuring the script to connect to MySQL
To output the data to mysql, you will need to include some details in the .env file so that the script knows how to access your database.  The login should have some elevated rights to create the database and table that will host your data. You will have to update the host, user, and pw parameters.  If you'd like to change the name of your database, you can also do that in the db item, otherwise keep it as the default book_parser.

```
{
    "url":"http://books.toscrape.com/",
    "app":"book_parser",
    "host": "yourDBHostname",
    "user":"yourDBUser",
    "pw" : "youDBPassword",
    "db":"book_parser",
    "logPath":"./log/",
    "dataPath":"./data/",
    "schemaFile":"schema.json",
    "charset":"utf8"
}
```

### Executing program
I attempted to make this script flexible enough to parse whichever category you wanted and offer you the categories through a list available through a helper command.  


* To receive the list of available categories to parse.
```
python3 book-parser.py -clist
```

* This is how you parse all books in the science and poetry categories to JSON
```
python3 book-parser.py -o json -c science -c poetry
```

* The script can offer you the data in either json, csv, or mySQL .  just update your -o parameter to either of those and it will output accordingly.


## Help

If you seek help you can pass -h to the script like this:
```
python3 book-parser.py -h
```

## Authors

Contributors names and contact info

Dom DaFonte
[@DomDaFonte](https://twitter.com/domdafonte)

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

I used a refactored version of an old web scraper I created that I branded python-data-tools
* [awesome-readme](https://github.com/TrasOsMontes/Python-Data-Tools)
