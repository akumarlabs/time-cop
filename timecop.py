# Install Beautiful Soup - a Python library for screen-scraping
# pip install beautifulsoup
# Install html5lib - a Python library for parsing and serializing HTML documents
# pip install html5lib

import urllib2, base64, re, smtplib, ConfigParser
from datetime import date, timedelta
from bs4 import BeautifulSoup
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def previous_weekday(todaysdate):
    todaysdate -= timedelta(days=1)
    while todaysdate.weekday() > 4: # Mon-Fri are 0-4
        todaysdate -= timedelta(days=1)
    return todaysdate

# Load configuration data from file
# Return list with index 0: URL, index 1: username, index 2: password, index 3: loggedHours, index 4: from, index 5: subject, index 6: smtp, index 7: port, index 8: emailUsername, index 9: emailPassword, index 10: defaultto, index 11: domain
def configLoader():
	config = ConfigParser.ConfigParser()
	config.read('timecop.config')
	return [config.get('jira-tempo-config','url'), config.get('jira-tempo-config','username'), config.get('jira-tempo-config','password'), config.get('jira-tempo-config','loggedHours'), config.get('email-config','from'), config.get('email-config','subject'), config.get('email-config','smtp'), config.get('email-config','port'), config.get('email-config','emailUsername'), config.get('email-config','emailPassword'), config.get('email-config','defaultto'), config.get('email-config','domain')]

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
			pattern = '\\' + credentials[11] + '$'
			developers.append(re.sub(pattern, '', str(frag['data-tempo-user'])) + credentials[11])
		# Check for cells with logged or missing hours
		elif 'td' in frag.name and ( all((w in frag['class'] for w in ['hours-completed', 'nav', 'hours'])) or all((w in frag['class'] for w in ['hours-missing', 'nav', 'hours'])) ):
			#print(frag.get_text(strip=True))
			hours.append(float(frag.get_text(strip=True)))

	dictionary = dict(zip(developers, hours))
	return dict((k, v) for k, v in dictionary.items() if v < float(credentials[3]))

# Note. Google blocks sign-in attempts from apps which do not use modern security standards. You can however, turn on/off this safety feature by going to the link below:
# https://www.google.com/settings/security/lesssecureapps
def sendNonComplianceEmails():
	fromAddress = credentials[4]
	toAddress = credentials[10]
	subject = credentials[5]
	msg = MIMEMultipart()
	msg['From'] = fromAddress
	msg['To'] = toAddress
	msg['Subject'] = subject
 
	body = str(stragglers)
	msg.attach(MIMEText(body, 'plain'))
 
	server = smtplib.SMTP(credentials[6], credentials[7])
	server.ehlo()
	server.starttls()
	server.login(credentials[8], credentials[9])
	#server = smtplib.SMTP('localhost')
	text = msg.as_string()
	server.sendmail(fromAddress, toAddress, text)
	server.quit()

credentials = configLoader()
pageResult = pageLoader()
stragglers = findStragglers()
sendNonComplianceEmails()

print stragglers

