import boto3
import json
import logging
import traceback
import os

print('Loading function')

collection = os.environ['REKOGNITION_FACE_COLLECTION']
rekognition = boto3.client('rekognition')
logger = logging.getLogger()


def lambda_handler(event, context):
    print('received event:' + json.dumps(event, indent=2))

    if event['RequestType'] == 'Delete':
        try:
            ret = rekognition.delete_collection(CollectionId=collection)
            if ret['ResponseMetadata']['HTTPStatusCode'] == 200:
                print('Resource deleted')
                return 'Rekognition collection deleted'
            return
        except:
            logger.error("error: {0}".format(traceback.format_exc()))
            return 'Rekognition collection deletion error: {0}'.format(traceback.format_exc())
    else:
        try:
            ret = rekognition.create_collection(
                CollectionId=collection)
            if ret['ResponseMetadata']['HTTPStatusCode'] == 200:
                print('Resource created')
                return 'Rekognition collection created'
        except rekognition.exceptions.ResourceAlreadyExistsException:
            print('Rekognition collection already exists')
        except:
            logger.error("error: {0}".format(traceback.format_exc()))
            return 'Rekognition collection creation error: {0}'.format(traceback.format_exc())
