#!/usr/bin/env bash

set -e

yarn add serverless-python-requirements@4.2.1
yarn global add serverless@1.31.0

sls deploy
