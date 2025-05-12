#!/usr/bin/env python3
import boto3
import os
import sys

def main():
    print("Starting error test script...")
    
    try:
        # Attempt to access a non-existent AWS resource will cause an error
        s3 = boto3.client('s3')
        
        # Attempt to access a non-existent bucket
        print("Attempting to access non-existent bucket...")
        response = s3.get_object(
            Bucket='this-bucket-does-not-exist-123456789',
            Key='this/file/does/not/exist.txt'
        )
        
        print("This line should never be reached")
        return 0
        
    except Exception as e:
        # Write error to stderr instead of stdout
        print(f"Error occurred: {str(e)}", file=sys.stderr)
        # Return non-zero error code
        return 1

if __name__ == "__main__":
    exit(main())