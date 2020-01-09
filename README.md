# AWS Rekognition Sample

## Usefull Links

*  [Build Your Own Face Recognition Service Using Amazon Rekognition](https://aws.amazon.com/fr/blogs/machine-learning/build-your-own-face-recognition-service-using-amazon-rekognition/)

## Required Tools

*  [AWS CLI](https://docs.aws.amazon.com/fr_fr/cli/latest/userguide/cli-chap-install.html)
*  [Pre-Commit](https://pre-commit.com/#install)
*  [Node.js](https://nodejs.org/en/)

## Installation

```
# Install javascript dependencies
$ npm install

# Install python dependencies
$ pipenv install

# Apply pre-commit hook on your git folder:
$ pre-commit install
```

### Configuration

The Makefile configuration file must be named `.env` and placed in the root of your source directory.

You can copy from the dist file:

```
$ cp .env.dist .env
```

Replace these values with your keys:

```
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

Then, test your configuration:

```
$ make me
```

You'll see your configured account.

## Deploy

Deploy the stack:

```
$ make deploy
$ make init-dataset
$ make test
```

## Cleanup

Remove all resources (you must empty the S3 bucket before):

```
$ make tear-down
```
