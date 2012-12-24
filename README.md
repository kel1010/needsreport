#The Needs Report#

Our goal is to create a better way for all individuals to have a voice in international development, prioritizing development projects from the ground up.

Individuals will report the top need in their community, and the location of their community. The information can be aggregated and mapped automatically. This will become a public tool for NGOs, governments, and individuals to track needs over time, and to compare expenditures vs. results.

The idea is a data aggregation and mapping platform - where data points and their magnitude are easily visible at first glance. Data will be collected using SMS from individuals in developing countries on an ongoing basis and displayed on an interactive web map.

##Installation##

Install pip:
http://pypi.python.org/pypi/pip

Install virtualenv:
pip install virtualenv

Create environment:

virtualenv --no-site-packages needs_env

Install packages:

source needs_env/bin/active

needs_env/bin/pip install -r needs/requirement.pip

Install MongoDB:

http://www.mongodb.org/downloads

##Data##

###Needs types###

Download https://docs.google.com/spreadsheet/ccc?key=0Aviwz_Rg5-8YdEVyYjVRaklCc2UxQ2prTTRqcmJlaWc#gid=0 as CSV file and call it types.csv

./manage.py types types.csv

###Countries###

Dump countries.json into needs_db

mongoimport -d needs_db -c countries --jsonArray --file countries.json

###Dummy Data###

./manage.py dummy_data

will create 1000 needs.  The location are capitals of countries in the countries table.
 
###Map Cluster###

I am using google map clusterer.  I downloaded the js file locally, but the source along with documents and examples can be found here:

http://google-maps-utility-library-v3.googlecode.com/svn/tags/markerclustererplus/2.0.9/

