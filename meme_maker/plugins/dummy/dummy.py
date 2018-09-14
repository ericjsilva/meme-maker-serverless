#!/usr/bin/env python
from meme_maker.plugins import subscribe


@subscribe(['post_get_image'])
def run(context):
    context.logger.info('Received context: {}'.format(context.to_dict()))
    return context
