#!/usr/bin/env python

import json
import logging
import os
import requests

from urlparse import parse_qs
from meme_maker.meme import Meme

LOG_FORMAT = "%(levelname)9s [%(asctime)-15s] %(name)s - %(message)s"


def get_value_from_command(args, key):
    try:
        value = next(arg for arg in args if arg.startswith('%s:' % key))
        args.remove(value)
        return ':'.join(value.split(':')[1:]), args
    except:
        return None, args


def prepare_response_content(text, public):
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


def quick_response(text, public=False):
    return prepare_response_content(text, public)


def delayed_response(text, response_url=None, public=False):
    response = prepare_response_content(text, public)

    r = requests.post(
        response_url,
        data=response['body'],
        headers=response['headers']
    )

    return r.text


def handler(event, context):
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    logger = logging.getLogger('meme')

    print event

    bucket = os.environ['bucket']
    params = parse_qs(event['body'])
    command = params['text'][0].split(' ') if 'text' in params else ''
    response_url = params['response_url'][0]
    user_name = params['user_name'][0]

    url, command = get_value_from_command(command, 'url')
    template, command = get_value_from_command(command, 'meme')
    text = ' '.join(command)
    print text

    if not template and not url:
        return quick_response('no parameters no meme no kek', public=True)
    delayed_response(None, response_url, public=True)

    meme = Meme(logger, template, url, text)
    meme_path = meme.make_meme(bucket)

    meme_url = 'https://{}.s3.amazonaws.com/{}'.format(bucket, meme_path)
    response_text = "@{}: here's your meme: {}".format(user_name, meme_url)

    return delayed_response(response_text, response_url, public=True)
