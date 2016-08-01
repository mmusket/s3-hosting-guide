from __future__ import print_function
import gzip
import os
import boto3
import argparse
import sys
import pathlib
from botocore.exceptions import ClientError
import threading
from multiprocessing.pool import ThreadPool
from mimetypes import MimeTypes
from shutil import copyfile

dontZip = ['.jpg','.png','.ttf','.woff','.woff2','.gif']

def getFiles(start):
    file_paths = []   
    for root, directories, files in os.walk(start):
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
        #output = client.upload_file(filePath, bucket_name, destname)           
        data = open(filePath, 'rb')
        ftype, encoding = MimeTypes().guess_type(filePath)
        conType = ftype if ftype is not None else encoding if encoding is not None else 'text/plain'    
        encType =  'gzip' if isZipFile(filePath) else None  
        s3.Object(bucket_name, destname).put(Body=data,ContentEncoding='gzip',ContentType=conType,ACL='public-read')
    except ClientError as err:
        print("Failed to upload artefact to S3.\n" + str(err))
        return False
    except IOError as err:
        print("Failed to access artefact in this directory.\n" + str(err))
        return False   
    return True


# def upload_to_s3(bucket_name, sourceDir, bucket_key):
#     print("Starting script")  
#     session = boto3.Session(profile_name='deploy')
#     client = session.client('s3')
#     uploadFileNames = getFiles(sourceDir)
#     print("Found " + len(uploadFileNames).__str__() + ' files')
#     for filename in uploadFileNames:      
#         try:
#             #filename = filename.replace('\\','/') #if on windows s3 wont seperate files in folders        
#             destname = os.path.join(*(filename.split('\\')[2:])).replace('\\','/')          
#             print ("Uploading file " + filename + ' to ' + destname)
#             client.upload_file(filename, bucket_name, destname)
#         except ClientError as err:
#             print("Failed to upload artefact to S3.\n" + str(err))
#             return False
#         except IOError as err:
#             print("Failed to access artefact in this directory.\n" + str(err))
#             return False
#     return True

# def main():

#     parser = argparse.ArgumentParser()
#     parser.add_argument("bucket", help="Name of the existing S3 bucket")
#     parser.add_argument("artefact", help="Name of the artefact to be uploaded to S3")
#     parser.add_argument("bucket_key", help="Name of the S3 Bucket key")
#     args = parser.parse_args()

#     if not upload_to_s3(args.bucket, args.artefact, args.bucket_key):
#         sys.exit(1)

# if __name__ == "__main__":
#     main()




filesToProcess = getFiles('dist')
print ('Found ' + len(filesToProcess).__str__() + ' files to process')
[zipFile(x,'out\\' + x) if isZipFile(x) else copyFile(x,'out\\' + x) for x in filesToProcess]
#upload_to_s3('upload-gzip-test-2','out\\dist\\','')
#[upload_file('upload-gzip-test-2',x) for x in getFiles('out\\dist\\')]


pool = ThreadPool(processes=40)
pool.map(lambda x : upload_file('upload-gzip-test-2',x), getFiles('out\\dist\\'))
#upload_file('upload-gzip-test-2','out\\dist\\index.html')