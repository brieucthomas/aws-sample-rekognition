import boto3
import os

s3 = boto3.resource('s3')

bucket = os.environ['S3_FACE_INDEX_BUCKET']

# Get list of objects for indexing
images = [
    ('dataset/albert-einstein/image01.jpeg', 'Albert Einstein'),
    ('dataset/albert-einstein/image02.jpeg', 'Albert Einstein'),
    ('dataset/albert-einstein/image03.jpeg', 'Albert Einstein'),
    ('dataset/niels-bohr/image01.jpeg', 'Niels Bohr'),
    ('dataset/niels-bohr/image02.jpeg', 'Niels Bohr'),
    ('dataset/niels-bohr/image03.jpeg', 'Niels Bohr')
]

print('Bucket: {}'.format(bucket))

# Iterate through list to upload objects to S3
for image in images:
    file = open(image[0], 'rb')
    object = s3.Object(bucket, image[0])
    print('Uploading {}...'.format(image[0]))
    ret = object.put(
        Body=file,
        Metadata={'FullName': image[1]}
    )

print('Dataset Complete.')
