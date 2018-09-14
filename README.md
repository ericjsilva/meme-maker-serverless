# meme-maker [![Build Status](https://travis-ci.org/ericjsilva/meme-maker-serverless.svg?branch=master)](https://travis-ci.org/ericjsilva/meme-maker-serverless)
Serverless API and Slack bot deployment for meme generator.

## Get it running
If you're here you're just a few minutes away from having your own meme generator.

#### Install dependencies
Requires node>=6.10
```bash
npm install --save serverless-python-requirements@4.2.1
npm install -g serverless@1.31.0
```

#### Verify your configuration

To deploy the application and be able to easily integrate it with Slack you need setup your AWS credentials, for which you have [a lot of options](https://serverless.com/framework/docs/providers/aws/guide/credentials/) (tl;dr: `aws configure` or `export AWS_ACCESS_KEY_ID= && export AWS_SECRET_ACCESS_KEY=`).

Proper AWS region needs to be configured in `serverless.yml`. Also `profile` can be configured there - if you don't want to use the default one.

Deploying requires few AWS permissions, full list can be found on [Serverless framework GitHub](https://github.com/serverless/serverless/issues/1439#issue-162824830).

#### Deploy
This command creates whole CloudFormation stack, including S3 bucket, API Gateway and Lambda function - might take a few minutes.
```bash
sls deploy
```

## Slack integration

Add to your Slack a [slash command](https://slack.com/apps/A0F82E8CA-slash-commands) and choose a command name you like (for example `/meme` is a great choice).

The only required change is located in the Integration Settings section. Paste to the `URL` field url which you got printed out after `sls deploy` command under `endpoints` field. You can also retreive it with `sls info` command.

Setup a name and icon and enjoy your memes!

**Usage**

To generate meme use following syntax:

`/command name url top text|bottom text`

For example:

`/meme pepe http://www.thewrap.com/wp-content/uploads/2016/09/1200.jpg make memes|not war`

Which will get back to you in a few seconds with ready meme. It will also create a template from passed url so you could use it later on without spcifying url:

`/meme pepe make memes|not war`


---

**Contributors**
- [x] [mkasprzyk](https://github.com/mkasprzyk)


