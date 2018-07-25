from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib
import datetime
import time
import botocore

print('Loading function')

rekognition = boto3.client('rekognition')


# --------------- Helper Functions to call Rekognition APIs ------------------


def detect_faces(bucket, key):
    response = rekognition.detect_faces(
        Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response


def detect_labels(bucket, key):
    response = rekognition.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}})

    # Sample code to write response to DynamoDB table 'MyTable' with 'PK' as Primary Key.
    # Note: role used for executing this Lambda function should have write access to the table.
    #table = boto3.resource('dynamodb').Table('MyTable')
    #labels = [{'Confidence': Decimal(str(label_prediction['Confidence'])), 'Name': label_prediction['Name']} for label_prediction in response['Labels']]
    #table.put_item(Item={'PK': key, 'Labels': labels})
    return response


def index_faces(bucket, key):
    # Note: Collection has to be created upfront. Use CreateCollection API to create a collecion.
    #rekognition.create_collection(CollectionId='BLUEPRINT_COLLECTION')
    response = rekognition.index_faces(
        Image={"S3Object": {"Bucket": bucket, "Name": key}}, CollectionId="household")
    # if len(response['FaceMatches']) == 0:
    #     print("Unrecognized face!")
    # else:
    #     print("face in the image: " + response['FaceMatches'][0]['Face']['FaceId'])
    return response


def compare_faces(bucket, key, source):
    response = rekognition.compare_faces(SimilarityThreshold=80,
                                         SourceImage={"S3Object": {
                                             "Bucket": "known-faces", "Name": source}},
                                         TargetImage={'S3Object': {'Bucket': bucket, 'Name': key}})

    return response


# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    startTime = time.time()
    table = boto3.resource(
        'dynamodb', region_name='eu-west-1').Table('local-stats')
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    # bucket = event['Records'][0]['s3']['bucket']['name']
    # key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    snsMsg = event['Records'][0]['Sns']['Message']
    print(snsMsg)
    snsJson = json.loads(snsMsg)
    bucket = snsJson['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(
        snsJson['Records'][0]['s3']['object']['key'].encode('utf8'))
    print('checking %s' % key)
    try:
        # Calls rekognition DetectFaces API to detect faces in S3 object
        #response = detect_faces(bucket, key)

        # Calls rekognition DetectLabels API to detect labels in S3 object
        #response = detect_labels(bucket, key)

        # Calls rekognition IndexFaces API to detect faces in S3 object and index faces into specified collection
        # response = index_faces(bucket, key)

        # Compare face
        # Names
        # TOOD read it from S3
        names = {"aysenur": 0, "halil": 0}
        responses = []
        detectedFace = {}
        faceLabel = 'unknown'
        for name, confidence in names.iteritems():
            print("checking " + name)
            source = name + '.jpg'
            print('key %s source %s' % (key, source))
            response = compare_faces(bucket, key, source)
            if len(response["FaceMatches"]) > 0:
                confidence = response["FaceMatches"][0]["Similarity"]
                detectedFace = response["FaceMatches"][0]
                print("detected " + name)
                faceLabel = name
                break
            else:
                print("nope, it's not " + name)

        if len(detectedFace) == 0:
            print("cannot recognize " + key)

        table_update_response = table.update_item(
            Key={
                'filename': key
            },
            UpdateExpression='SET duration_lambda = :dur, result_lambda = :result',
            ExpressionAttributeValues={
                ':dur': str(time.time() - startTime),
                ':result': faceLabel
            }
        )
        print(table_update_response)
        return detectedFace
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidParameterException':
            print('failed to find face ' + e.response['Error']['Message'])
            table_update_response = table.update_item(
                Key={
                    'filename': key
                },
                UpdateExpression='SET duration_lambda = :dur, result_lambda = :result',
                ExpressionAttributeValues={
                    ':dur': str(time.time() - startTime),
                    ':result': 'no-face-detected'
                }
            )
        else:
            print("boto returned error: " + str(e))
            raise e
    except Exception as e:
        print("cought exception during the process: " + str(e))
        raise e
