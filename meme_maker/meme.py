#!/usr/bin/env python

import hashlib
import os
import io
import requests
import tempfile
import textwrap
import time
import sys

from .plugins import PluginsLoader
from PIL import Image, ImageDraw, ImageFont

import boto3


plugins = PluginsLoader()
plugins.discover()


class Storage:

    def __init__(self, logger):
        self.logger = logger
        self.type = 'local'
        self.bucket = None
        self.path = None
        self.s3 = None

    def setup_s3_client(self):
        self.s3 = boto3.client('s3')

    def get_s3_file(self, path):
        return self.s3.get_object(
            Bucket=self.bucket,
            Key=path
        )['Body'].read()

    def create_dir_structure(self):
        directories = (
            'me',
            'me/me',
            'me/mplate'
        )

        for directory in directories:
            path = os.path.join(self.path, directory)
            if not os.path.isdir(path):
                os.makedirs(path)

    def recognize_storage(self, path):
        if os.path.isdir(path):
            self.type = 'local'
            self.path = path
            self.create_dir_structure()
            self.logger.info('recognized storage: %s' % self.type)
            return

        self.setup_s3_client()
        bucket = path.split('/')[0]
        path = path.split('/')[1:]
        path = '/'.join(path) + '/' if path else ''

        try:
            self.s3.list_objects(
                Bucket=bucket,
                Prefix=path
            )
        except Exception as e:
            self.logger.error('Specified path not recognized as local or s3: %s' % e)
            sys.exit(1)

        self.type = 's3'
        self.bucket = bucket
        self.path = path
        self.logger.info('recognized storage: %s' % self.type)


class Meme:

    def __init__(self, logger, template, url, text):
        self.logger = logger
        self.template_name = template
        self.template_path = None
        self.meme_path = None
        self.tmp_path = None
        self.url = url
        self.text = text
        self.filetype = 'png'
        self.storage = Storage(self.logger)
        self.font_path = os.path.join(os.path.dirname(__file__),
                                      'assets/impact.ttf')

    def set_paths(self):
        self.template_path = '%sme/mplate/%s.%s' % (
            self.storage.path, self.template_name, self.filetype)
        timestamp = int(time.time())
        self.meme_path = '%sme/me/%s-%s.%s' % (
            self.storage.path, self.template_name, timestamp, self.filetype)

    def generate_template_name(self):
        return hashlib.md5(self.url.encode('utf-8')).hexdigest()

    @plugins.dispatch
    def get_image_from_url(self):
        self.logger.info('downloading %s' % self.url)
        try:
            image = requests.get(self.url)
        except requests.exceptions.RequestException as exc:
            self.logger.error('Unable to retreive URL: %s' % exc)

        try:
            self.image = Image.open(io.BytesIO(image.content)).convert('RGB')
        except IOError:
            self.logger.error('Given URL doesnt seems to be a proper image')
        except Exception as e:
            self.logger.error('Unable to process the image: %s' % e)

    def store_image(self, path):
        self.logger.info('storing image at %s' % path)
        tmp_path = '%s.%s' % (tempfile.NamedTemporaryFile().name,
                              self.filetype)

        self.image.save(tmp_path)
        if self.storage.type == 'local':
            self.image.save(path)

        elif self.storage.type == 's3':
            self.storage.s3.put_object(
                Bucket=self.storage.bucket,
                ACL='public-read',
                Body=open(tmp_path, 'rb'),
                ContentType='image/%s' % self.filetype,
                Key=path
            )

    @plugins.dispatch
    def get_image(self, path):
        self.logger.info('getting image from %s' % path)
        if self.storage.type == 'local':
            if not os.path.isfile(self.template_path):
                return False
            with open(self.template_path, 'rb') as f:
                image = f.read()
        elif self.storage.type == 's3':
            try:
                image = self.storage.get_s3_file(path)
            except Exception as e:
                self.logger.info('Unable to get image from S3: %s' % e)
                return False

        self.image = Image.open(io.BytesIO(image)).convert('RGB')

        return True

    def find_longest_line(self, text):
        longest_width = 0
        longest_line = ''
        for line in text:
            width = self.draw.textsize(line, font=ImageFont.truetype(self.font_path, 20))[0]
            if width > longest_width:
                longest_width = width
                longest_line = line

        return longest_line

    def get_font_measures(self, text, font_size, ratio):
        measures = {}
        measures['font'] = ImageFont.truetype(self.font_path, size=font_size)
        measures['width'] = self.draw.textsize(text, font=measures['font'])[0]
        measures['ratio'] = measures['width'] / float(self.image.width)
        measures['ratio_diff'] = abs(ratio - measures['ratio'])

        return measures

    def optimize_font(self, text):
        """Fuckin' magnets how do they work"""
        font_min_size = 12
        font_max_size = 70
        font_size_range = range(font_min_size, font_max_size + 1)

        longest_text_line = self.find_longest_line(text)

        # set min/max ratio of font width to image width
        min_ratio = 0.7
        max_ratio = 0.9
        perfect_ratio = min_ratio + (max_ratio - min_ratio)/2
        ratio = 0

        while (ratio < min_ratio or ratio > max_ratio) and len(font_size_range) > 2:
            measures = {
                'top': self.get_font_measures(
                           text=longest_text_line,
                           font_size=font_size_range[-1],
                           ratio=perfect_ratio
                       ),
                'low': self.get_font_measures(
                           text=longest_text_line,
                           font_size=font_size_range[0],
                           ratio=perfect_ratio
                       )
            }

            half_index = len(font_size_range)/2
            if measures['top']['ratio_diff'] < measures['low']['ratio_diff']:
                closer = 'top'
                font_size_range = font_size_range[int(half_index):-1]
            else:
                closer = 'low'
                font_size_range = font_size_range[0:half_index]

            ratio = measures[closer]['ratio']
            witdh = measures[closer]['width']
            font = measures[closer]['font']

        width = self.draw.textsize(longest_text_line, font=font)[0]

        return font, width

    def set_text_wrapping(self, text_length):
        if text_length <= 32:
            wrapping = 32
        elif text_length > 100:
            wrapping = 10 + text_length / 3
        elif text_length > 32:
            wrapping = 5 + text_length / 2
        self.logger.info('wrapping {}'.format(wrapping))

        return wrapping

    def prepare_text(self, text):
        if not text:
            return '', 0
        if type(text) == list:
            text = text[0]
        self.logger.info('preparing meme text: {}'.format(text))
        wrapping = self.set_text_wrapping(len(text))
        text = text.strip().upper()
        text = textwrap.wrap(text, wrapping)
        font, text_width = self.optimize_font(text)

        text = '\n'.join(text)

        return text, text_width, font

    def draw_text(self, xy, text, font):
        self.logger.info('drawing meme text: %s' % text)
        x = xy[0]
        y = xy[1]

        o = 1

        xys = (
            (x+o, y),
            (x-o, y),
            (x+o, y+o),
            (x-o, y-o),
            (x-o, y+o),
            (x, y-o),
            (x, y+o)
        )

        for xy in xys:
            self.draw.multiline_text(
                xy,
                text,
                fill='black',
                font=font,
                align='center'
            )

        self.draw.multiline_text(
            (x, y),
            text,
            fill='white',
            font=font,
            align='center'
        )

    def draw_meme(self):
        self.logger.info('drawing meme')
        self.draw = ImageDraw.Draw(self.image)

        margin_xy = (
            0,
            self.image.height/18
        )

        text_top = self.text.split('|')[0]
        if text_top:
            text_top, text_top_width, top_font = self.prepare_text(text_top)
            top_xy = (
                ((self.image.width - text_top_width)/2),
                (margin_xy[1])
            )
            self.draw_text(top_xy, text_top, top_font)

        text_bottom = self.text.split('|')[1:]
        if text_bottom:
            text_bottom, text_bottom_width, bottom_font = self.prepare_text(text_bottom)
            bottom_xy = [
                ((self.image.width - text_bottom_width)/2),
                (self.image.height - bottom_font.getsize(text_bottom)[1]*len(text_bottom.split('\n')) - margin_xy[1])
            ]
            self.draw_text(bottom_xy, text_bottom, bottom_font)

    def make_meme(self, path):
        self.storage.recognize_storage(path)
        self.set_paths()

        if self.url:
            self.get_image_from_url()
            if not self.template_name:
                self.generate_template_name()
            if not self.get_image(self.template_path):
                self.store_image(self.template_path)
        elif self.template_name:
            self.get_image(self.template_path)
        else:
            self.logger.error('Not enough parameters passed')

        self.draw_meme()
        self.store_image(self.meme_path)

        return self.meme_path
