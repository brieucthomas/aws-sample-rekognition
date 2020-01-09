# ENV
# This will load and export variables from an env files
include .env
MAKEFILE_DIR=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))
PIPENV_DONT_LOAD_ENV=1
PIPENV_VERBOSITY=-1
#SLS_DEBUG=*
export

# HELP
# This will output the help for each task
# thanks to https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

me: ## Show your current AWS identity
	@aws sts get-caller-identity --output json

validate: ## Validate all compliances
	@pipenv run pre-commit run --all-files

init-dataset: ## Init dataset
	@pipenv run python scripts/dataset.py

deploy: validate ## Deploy face detection demo
	@node_modules/.bin/serverless deploy --force
	@node_modules/.bin/serverless invoke --function CreateFaceCollection --data '{"RequestType": "Create"}'

test:
	@aws s3 cp tests/image01.jpeg s3://$(S3_FACE_SEARCH_BUCKET)/image01.jpeg
	@aws s3 cp tests/image02.jpeg s3://$(S3_FACE_SEARCH_BUCKET)/image02.jpeg
	@aws s3 cp tests/image03.jpeg s3://$(S3_FACE_SEARCH_BUCKET)/image03.jpeg

tear-down: ## Remove face detection demo
	@read -p "Are you sure that you want to remove face-detection application? [y/N]: " sure && [ $${sure:-N} = y ]
	@aws s3 rm s3://$(S3_FACE_INDEX_BUCKET)/ --recursive
	@aws s3 rm s3://$(S3_FACE_SEARCH_BUCKET)/ --recursive
	@node_modules/.bin/serverless invoke --function CreateFaceCollection --data '{"RequestType": "Delete"}'
	@node_modules/.bin/serverless remove --force
