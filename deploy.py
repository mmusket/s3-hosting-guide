from __future__ import print_function
import os
import boto3
from botocore.exceptions import ClientError
from mimetypes import MimeTypes
import gzip
from shutil import copyfile
import threading
from multiprocessing.pool import ThreadPool

dontZip = ['.jpg','.png','.ttf','.woff','.woff2','.gif']
bucketName = 'blank-website'
sourceDir = 'dist'
stagingDir = 'out\\'

def getFiles(baseFolder):
    file_paths = []   
    for root, directories, files in os.walk(baseFolder):
        for filename in files:         
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  
    return file_paths  

def zipFile(input, output):
    print ('Zipping ' + input)
    dirname = os.path.dirname(output)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(input) as f_in, gzip.open(output, 'wb') as f_out:
        f_out.writelines(f_in)

def copyFile(input, output):
    print ('Copying ' + input)
    dirname = os.path.dirname(output)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    copyfile(input, output)

def isZipFile(fileName):
    extension = os.path.splitext(fileName)[1]
    if extension in dontZip:
        return False
    return True

def upload_file(bucket_name,filePath):
    session = boto3.Session(profile_name='deploy')
    client = session.client('s3')
    s3 = session.resource('s3')
    destname = os.path.join(*(filePath.split('\\')[2:])).replace('\\','/')          
    print ("Uploading file " + filePath + ' to ' + destname)
    try:      
        data = open(filePath, 'rb')
        ftype, encoding = MimeTypes().guess_type(filePath)
        conType = ftype if ftype is not None else encoding if encoding is not None else 'text/plain'    
        encType =  'gzip' if isZipFile(filePath) else ''  
        s3.Object(bucket_name, destname).put(Body=data,ContentEncoding=encType,ContentType=conType,ACL='public-read')
    except ClientError as err:
        print("Failed to upload artefact to S3.\n" + str(err))
        return False
    except IOError as err:
        print("Failed to access artefact in this directory.\n" + str(err))
        return False   
    return True

[zipFile(x,stagingDir + x) if isZipFile(x) else copyFile(x,stagingDir + x) for x in getFiles(sourceDir)]
pool = ThreadPool(processes=40)
pool.map(lambda x : upload_file(bucketName,x), getFiles(stagingDir))
