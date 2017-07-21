# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


#SQL - https://cloud.google.com/sql/docs/mysql/connect-admin-ip#configure-instance-mysql
#Options for cinnecting - https://cloud.google.com/sql/docs/mysql/external-connection-methods
#SQL connection - https://cloud.google.com/sql/docs/mysql/connect-admin-ip

# [START app]
import datetime
import logging
import os
import socket
import time
import json
from slackclient import SlackClient
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

logging.basicConfig(level=logging.INFO)

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
app = Flask(__name__)

def is_ipv6(addr):
    """Checks if a given address is an IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except socket.error:
        return False

# Environment variables are defined in app.yaml.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime())
    user_ip = db.Column(db.String(46))

    def __init__(self, timestamp, user_ip):
        self.timestamp = timestamp
        self.user_ip = user_ip

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    logging.info("Hello world being called!")

    user_ip = request.remote_addr
    logging.info("Got user ip:" + user_ip)

    # Keep only the first two octets of the IP address.
    if is_ipv6(user_ip):
        user_ip = ':'.join(user_ip.split(':')[:2])
    else:
        user_ip = '.'.join(user_ip.split('.')[:2])

    visit = Visit(
        user_ip=user_ip,
        timestamp=datetime.datetime.utcnow()
    )

    db.session.add(visit)
    db.session.commit()

    visits = Visit.query.order_by(sqlalchemy.desc(Visit.timestamp)).limit(10)

    results = [
        'Time: {} Addr: {}'.format(x.timestamp, x.user_ip)
        for x in visits]

    output = 'Last 10 visits:\n{}'.format('\n'.join(results))

    return 'Hello World Rafal test with new me: ' + BOT_ID + '<br />'+output, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
    #logging.warning("Starting the slack bot stuff")
    #logging.info("BOT_ID: " + BOT_ID)
    #logging.info("SLACK_BOT_TOKEN: " + SLACK_BOT_TOKEN)

    #READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    #if slack_client.rtm_connect():
    #    logging.warning("StarterBot connected and running!")
    #    while True:
    #        raw_cmd = slack_client.rtm_read()
    #        if raw_cmd and len(raw_cmd) > 0:
    #            n = 0
    #            for msg in raw_cmd:
    #                n = n+1
    #                if 'type' in msg:
    #                    logging.info( "Msg n: " + str(n) + str(msg['type']) )
    #                #    logging.info("[",n,"] Command type:")
    #        #command, channel = parse_slack_output(raw_cmd)
    #        #if command and channel:
    #        #    handle_command(command, channel)
    #        time.sleep(READ_WEBSOCKET_DELAY)

    #else:
    #    logging.warning("Connection failed. Invalid Slack token or bot ID?")





# [END app]
