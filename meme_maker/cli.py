#!/usr/bin/env python

import click
import logging

from .meme import Meme

LOG_FORMAT = "%(levelname)9s [%(asctime)-15s] %(name)s - %(message)s"
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--meme', '-m', help='meme template to be used')
@click.option('--url', '-u', help='image url')
@click.argument('text', nargs=-1)
def cli(meme, url, text):
    if not meme or not url:
        raise click.BadParameter('No parameters specified')
    template = meme
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    logger = logging.getLogger('meme')

    meme = Meme(logger, template, url, text[0])
    meme.make_meme('/tmp/')


if __name__ == '__main__':
    cli()
