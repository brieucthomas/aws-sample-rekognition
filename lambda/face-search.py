import boto3
import io
import os
import uuid
import time
import decimal
import urllib
import json
from PIL import Image

print('Loading function')

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client('rekognition')

collection = os.environ['REKOGNITION_FACE_COLLECTION']
index_table = os.environ['DYNAMODB_FACE_INDEX_TABLE']
search_table = os.environ['DYNAMODB_FACE_SEARCH_TABLE']

# --------------- Helper Functions ------------------


def round_float_to_decimal(float_value):
    """
    Convert a floating point value to a decimal that DynamoDB can store,
    and allow rounding.
    """

    # Perform the conversion using a copy of the decimal context that boto3
    # uses. Doing so causes this routine to preserve as much precision as
    # boto3 will allow.
    with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as decimalcontext:
        # Allow rounding.
        decimalcontext.traps[decimal.Inexact] = 0
        decimalcontext.traps[decimal.Rounded] = 0
        decimal_value = decimalcontext.create_decimal_from_float(float_value)
        # print("float: {}, decimal: {}".format(float_value, decimal_value))

        return decimal_value


def read_image_from_s3(bucket, key):
    file_stream = s3.Bucket(bucket).Object(key).get()['Body']
    return Image.open(file_stream)


def patch_image_metadata(bucket, key, metadata):
    object = s3.Object(bucket, key)
    object.metadata.update(metadata)
    object.copy_from(CopySource={'Bucket': bucket, 'Key': key},
                     Metadata=object.metadata, MetadataDirective='REPLACE')


def image_binary(image):
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    return stream.getvalue()


def detect_faces(image):
    faces = []
    image_width = image.size[0]
    image_height = image.size[1]

    response = rekognition.detect_faces(
        Image={'Bytes': image_binary(image)}
    )

    # Crop face from image
    for face in response['FaceDetails']:
        box = face['BoundingBox']
        x1 = int(box['Left'] * image_width) * 0.9
        y1 = int(box['Top'] * image_height) * 0.9
        x2 = int(box['Left'] * image_width + box['Width'] * image_width) * 1.10
        y2 = int(box['Top'] * image_height + box['Height'] * image_height) * 1.10
        image_crop = image.crop((x1, y1, x2, y2))

        faces.append({
            'Box': {
                'X1': round_float_to_decimal(x1),
                'X2': round_float_to_decimal(x2),
                'Y3': round_float_to_decimal(y1),
                'Y1': round_float_to_decimal(y2)
            },
            'Image': image_crop
        })

    return faces


def search_faces_by_image(collection, image, threshold=80):
    response = rekognition.search_faces_by_image(
        CollectionId=collection,
        Image={'Bytes': image_binary(image)},
        FaceMatchThreshold=threshold,
        MaxFaces=1,
    )

    if not response['FaceMatches']:
        return []

    face = response['FaceMatches'][0]['Face']
    face_id = face['FaceId']
    confidence = face['Confidence']

    table = dynamodb.Table(index_table)
    person = table.get_item(
        Key={'RekognitionId': face_id}
    )

    return {
        'RekognitionId': face['FaceId'],
        'FullName': person['Item']['FullName'],
        'Confidence': round_float_to_decimal(confidence)
    }


def write_result(region, bucket, key, matches):
    item = {
        'SearchId': str(uuid.uuid1()),
        'ImageUrl': 'http://{}.s3-{}.amazonaws.com/{}'.format(bucket, region, key),
        'FaceCount': len(matches),
        'Faces': matches,
        'CreatedAt': int(time.time())
    }

    table = dynamodb.Table(search_table)
    table.put_item(Item=item)

    return item['SearchId']

# --------------- Main handler ------------------


def lambda_handler(event, context):
    print('received event:' + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    region = event['Records'][0]['awsRegion']

    try:
        # Read image from S3
        image = read_image_from_s3(bucket, key)

        # Detect all faces
        faces = detect_faces(image)

        face_matches = []

        for face in faces:
            face_matches.append({
                'Box': face['Box'],
                'Result': search_faces_by_image(collection, face['Image'])
            })

        # Commit result to DynamoDB
        search_id = write_result(region, bucket, key, face_matches)

        # Update image metadata
        patch_image_metadata(bucket, key, {
            'searchid': search_id
        })

        response = {
            'SearchId': search_id
        }

        # Print response to console.
        print(response)

        return response
    except Exception as e:
        print(e)
        print("Error processing {} from bucket {}. ".format(key, bucket))
        raise e
