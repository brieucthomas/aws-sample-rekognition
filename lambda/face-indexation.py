import boto3
import urllib
import os

print('Loading function')

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

collection = os.environ['REKOGNITION_FACE_COLLECTION']
index_table = os.environ['DYNAMODB_FACE_INDEX_TABLE']

# --------------- Helper Functions ------------------


def index_faces(collection, bucket, key):
    response = rekognition.index_faces(
        Image={
            'S3Object':
            {
                'Bucket': bucket,
                'Name': key
            }
        },
        CollectionId=collection
    )

    return response


def update_index(tableName, faceId, fullName):
    table = dynamodb.Table(tableName)
    table.put_item(Item={
        'RekognitionId': faceId,
        'FullName': fullName
    })

# --------------- Main handler ------------------


def lambda_handler(event, context):

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    try:

        # Calls Amazon Rekognition IndexFaces API to detect faces in S3 object
        # to index faces into specified collection
        response = index_faces(collection, bucket, key)

        # Commit faceId and full name object metadata to DynamoDB
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            face_id = response['FaceRecords'][0]['Face']['FaceId']

            ret = s3.head_object(Bucket=bucket, Key=key)
            person_full_name = ret['Metadata']['fullname']

            update_index(index_table, face_id, person_full_name)

        # Print response to console.
        print(response)

        return response
    except Exception as e:
        print(e)
        print('Error processing {} from bucket {}. '.format(key, bucket))
        raise e
