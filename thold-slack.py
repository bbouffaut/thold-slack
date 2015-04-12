#!/usr/bin/python
# - Copyleft 2015 - Jim Boswell

'''
This Python script is designed to ingest a Cacti THOLD email message as piped input from sendmail
and post the contents to a Slack channel as a rich format 'attachment' message
(https://api.slack.com/docs/attachments)

*It is highly recommended to run this through sendmail restricted shell (smrsh)*

    setup sendmail by doing the following, or manually editing /etc/aliases
    you may, use any alias you choose,  example below uses 'thold-slack'

    sudo echo "thold-slack: | /etc/smrsh/thold-slack.py" >> /etc/aliases
    sudo newaliases

    You will then need to setup Cacti, see README.md

'''

# import modules 
import sys
import email
from email import parser, FeedParser
from email.Iterators import typed_subpart_iterator
import urllib2,json

#### BEGIN GLOBAL VARIABLES ####
    ''' 
    You need to edit 'slack_webhook_url' with a webhook URL configured at:
    Slack Webhook URL (https://<domain>.slack.com/services/new/incoming-webhook)
    '''
slack_webhook_url   =   '<your Slack webhook URL goes here>' 

slack_channel       =   '#random'  # modify this to your liking, ex: #alerts
slack_usernmae      =   'Cacti THOLD' # the username reported in channel
slack_icon_emoji    =   ':cactus:' # any valid Slack emoji code,  defaults to cactus becasue Cacti
slack_title_link    =   "<insert URL to your THOLD alerts>" #ex: "https://<your-server>/cacti/plugins/thold/thold_graph.php?sort_column=lastread&sort_direction=DESC"

# you can use Slack API colors: good, warning, danger or any HEX value
thold_alert_color    = 'danger'
thold_warning_color  = 'warning'
thold_default_color  = '#439FE0' # a nice blue for any notice not ALERT or WARNING in subject line
#### END GLOBAL VARIABLES #####

def main():

    # read in piped socket as 'data'
    data = sys.stdin.readlines()

    # create email parser
    feed = email.parser.FeedParser()

    # read in our stdin into FeedParser feed
    for line in data:
        feed.feed(line)

    # call feed close to create mail object
    mail = feed.close()

    # DEBUG code
    #message = get_body(mail)
    #print message

    # determine Slack attachment color
    # allows for nice color coding of msgs
    if mail['subject'].startswith('ALERT'):
        color = thold_alert_color
    elif mail['subject'].startswith('WARNING'):
        color = thold_warning_color
    else:
     color = thold_default_color


    # build payload (https://api.slack.com/docs/attachments)
    payload = {
        'channel': slack_channel,
        'username': slack_usernmae,
        'icon_emoji': slack_icon_emoji,
        'attachments': [
            {
                "fallback": mail['subject'],
                "pretext": "",
                "title": mail['subject'],
                "title_link": slack_title_link,
                "text": message,
                "color": color
            }
        ]
    }


    req = urllib2.Request(slack_webhook_url)
    req.add_header('Content-Type','application/json')

    # JSONify our POST data
    postdata = json.dumps(payload)

    # POST data to Slack API
    try:
        urllib2.urlopen(req,postdata)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print e.read()
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        print "POST to Slack.com successful"
        # everything is fine

def get_charset(message, default="ascii"):
    """Get the message charset"""

    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default

def get_body(message):
    """Get the body of the email message"""

    if message.is_multipart():
        #get the plain text version only
        text_parts = [part
                      for part in typed_subpart_iterator(message,
                                                         'text',
                                                         'plain')]
        body = []
        for part in text_parts:
            charset = get_charset(part, get_charset(message))
            body.append(unicode(part.get_payload(decode=True),
                                charset,
                                "replace"))

        return u"\n".join(body).strip()

    else: # if it is not multipart, the payload will be a string
          # representing the message body
        body = unicode(message.get_payload(decode=True),
                       get_charset(message),
                       "replace")
        return body.strip()

if __name__ == '__main__':
  main()