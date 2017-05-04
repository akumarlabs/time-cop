# Install Beautiful Soup - a Python library for screen-scraping
# pip install beautifulsoup
# Install html5lib - a Python library for parsing and serializing HTML documents
# pip install html5lib

import urllib2, base64, ConfigParser
from datetime import date, timedelta
from bs4 import BeautifulSoup

def previous_weekday(todaysdate):
    todaysdate -= timedelta(days=1)
    while todaysdate.weekday() > 4: # Mon-Fri are 0-4
        todaysdate -= timedelta(days=1)
    return todaysdate

# Load configuration data from file
# Return list with index 0: URL, index 1: username, index 2: password, index 3: loggedHours
def configLoader():
	config = ConfigParser.ConfigParser()
	config.read('timecop.config')
	return [config.get('jira-tempo-config','url'), config.get('jira-tempo-config','username'), config.get('jira-tempo-config','password'), config.get('jira-tempo-config','loggedHours')]

# Load JIRA Tempo Team Time Tracking page (with credentials loaded from configuration file)
def pageLoader():
	request = urllib2.Request(credentials[0] + str(previous_weekday(date.today())))
	base64string = base64.b64encode('%s:%s' % (credentials[1], credentials[2]))
	request.add_header("Authorization", "Basic %s" % base64string)   
	return urllib2.urlopen(request)

# Find all team members that have not logged the number of hours specified in the configuration file	
def findStragglers():
	soup = BeautifulSoup(pageResult, "html5lib")
	fragment = soup.findAll(True, {"class":["username","hours-completed","hours-missing"]})
	developers = []
	hours = []
	for frag in fragment:
		# Check if the data-tempo-user attribute exists (which contains the username)
		if 'data-tempo-user' in frag.attrs:
			#print(frag['data-tempo-user'])
			developers.append(str(frag['data-tempo-user']))
		# Check for cells with logged or missing hours
		elif 'td' in frag.name and ( all((w in frag['class'] for w in ['hours-completed', 'nav', 'hours'])) or all((w in frag['class'] for w in ['hours-missing', 'nav', 'hours'])) ):
			#print(frag.get_text(strip=True))
			hours.append(float(frag.get_text(strip=True)))

	dictionary = dict(zip(developers, hours))
	return dict((k, v) for k, v in dictionary.items() if v < float(credentials[3]))


credentials = configLoader()
pageResult = pageLoader()
stragglers = findStragglers()

print stragglers

