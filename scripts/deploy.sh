#!/usr/bin/env bash

set -e

yarn add serverless-python-requirements@2.0.0
yarn global add serverless@1.5.0

sls deploy
