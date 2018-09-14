consy
#!/usr/bin/env python

import datetime
import json
import logging
import os
import sys
import requests

from urlparse import parse_qs
from meme_maker.meme import Meme

LOG_FORMAT = "%(levelname)9s [%(asctime)-15s] %(message)s"
START_TIME = datetime.datetime.now()
TIMEOUT_THRESHOLD = 2.5


def setup_logger():
    """
    Remove default AWS Lambda logging handlers and add new one with
    defined format.
    """

    logger = logging.getLogger()

    for handler in logger.handlers:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger


def get_value_from_command(args, key):
    """
    Extract value of given key from list-formatted command.
    Return both value and list command shorter of wanted key:value.
    """

    try:
        value = next(arg for arg in args if arg.startswith('%s:' % key))
        args.remove(value)
        return ':'.join(value.split(':')[1:]), args
    except:
        return None, args


def prepare_response_content(text, public):
    """
    Return formatted data and parameters required to send back http request.
    """

    response = {}

    data = {}
    if text:
        data['text'] = text
    if public:
        data['response_type'] = 'in_channel'
    response['body'] = json.dumps(data)

    response['headers'] = {'Content-Type': 'application/json'}
    response['statusCode'] = 200

    return response


def response(text, response_url=None, public=False):
    """
    Based on execution time decide and proceed with regular
    or delayed response/
    """

    running_time = (datetime.datetime.now()-START_TIME).total_seconds()

    if running_time > TIMEOUT_THRESHOLD:
        return delayed_response(text, response_url, public)

    return quick_response(text, public)


def quick_response(text, public):
    """Quick response by return to Api Gateway."""

    return prepare_response_content(text, public)


def delayed_response(text, response_url, public):
    """Delayed response by request to Slack endpoint."""

    response = prepare_response_content(text, public)

    r = requests.post(
        response_url,
        data=response['body'],
        headers=response['headers']
    )

    return r.text


def handler(event, context):
    """AWS Lambda handler"""

    logger = setup_logger()

    logger.info(event)

    bucket = os.environ['bucket']
    params = parse_qs(event['body'])
    command = params['text'][0].split(' ') if 'text' in params else ''
    response_url = params['response_url'][0]
    user_name = params['user_name'][0]

    url, command = get_value_from_command(command, 'url')
    template, command = get_value_from_command(command, 'meme')
    text = ' '.join(command)

    if not template and not url:
        return response('no parameters no meme no kek',
                        response_url, public=True)

    meme = Meme(logger, template, url, text)
    meme_path = meme.make_meme(bucket)

    meme_url = 'https://{}.s3.amazonaws.com/{}'.format(bucket, meme_path)
    response_text = "@{}: here's your meme: {}".format(user_name, meme_url)

    return response(response_text, response_url, public=True)
