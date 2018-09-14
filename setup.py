#!/usr/bin/env python
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist
from setuptools.command.egg_info import egg_info

import unittest
import pip

import os

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


class SetupTypes:
    SERVERLESS = 'serverless'
    BASE = 'base'
    TEST = 'test'
    PROD = 'prod'
    DEV = 'dev'

    all = [SERVERLESS, DEV, TEST, BASE, PROD]

    @staticmethod
    def requirements(setup_type):
        requirements_path_pattern = 'requirements/{setup_type}.txt'
        return requirements_path_pattern.format(
            setup_type=setup_type
        )


class CustomCommand(object):
    def prepare_requirements(self, setup_type):
        requirements = os.path.join(os.getcwd(),
                                    SetupTypes.requirements(setup_type))
        assert os.path.exists(requirements), 'Invalid requirements path!'
        return requirements

    def prepare_install_requires(self, setup_type=SetupTypes.BASE):
        install_requires = []
        parsed_requirements = pip.req.parse_requirements(
            self.prepare_requirements(setup_type), session='nevermind')
        for line in parsed_requirements:
            install_requires.append(str(line.req))
        return install_requires

    def update_extras_requires(self):
        self.distribution.extras_require = {}
        for setup_type in SetupTypes.all:
            self.distribution.extras_require[
                setup_type] = self.prepare_install_requires(setup_type)


def command_factory(base_command):
    class Command(base_command, CustomCommand):
        def run(self):
            self.update_extras_requires()
            super(Command, self).run()

    return Command


class CustomInstall(command_factory(install)):
    pass


class CustomDevelop(command_factory(develop)):
    pass


class CustomSdist(command_factory(sdist)):
    pass


class CustomEggInfo(command_factory(egg_info)):
    pass


def tests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('meme_maker.tests', pattern='test_*.py')
    return test_suite


setup(name="meme-maker",
      license="MIT",
      version='1.0',
      description="CLI, API, and Slack bot to generate memes.",
      maintainer="Eric Silva",
      maintainer_email="ericjsilva@gmail.com",
      author="Jacek Szubert",
      author_email="jacek.szubert@gmail.com",
      url="https://github.com/ericjsilva/meme-maker-serverless",
      keywords="meme, memes, slack, bot, api, cli, generator, aws, serverless, lambda",
      classifiers=["Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "Programming Language :: Python",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      packages=find_packages(),
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'meme-maker = meme_maker.__main__:cli',
          ]
      },
      cmdclass={
          'install': CustomInstall,
          'develop': CustomDevelop,
          'sdist': CustomSdist,
          'egg_info': CustomEggInfo
      },
      test_suite='setup.tests'
      )
