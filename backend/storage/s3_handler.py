import boto3
from botocore.exceptions import ClientError
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class S3Handler:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'robotcem-stl-files')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
    
    async def upload_stl(self, local_path: Path, job_id: str) -> str:
        """Upload STL file to S3 and return public URL"""
        
        s3_key = f"designs/{job_id}/{local_path.name}"
        
        try:
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/sla',
                    'ACL': 'public-read'
                }
            )
            
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded STL to S3: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def upload_metadata(self, local_path: Path, job_id: str) -> str:
        """Upload metadata JSON to S3"""
        
        s3_key = f"designs/{job_id}/{local_path.name}"
        
        try:
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/json',
                    'ACL': 'public-read'
                }
            )
            
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
        except ClientError as e:
            logger.error(f"S3 metadata upload failed: {e}")
            raise
    
    async def delete_design(self, job_id: str):
        """Delete all files for a design"""
        
        prefix = f"designs/{job_id}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects}
                )
                logger.info(f"Deleted {len(objects)} objects from S3 for job {job_id}")
                
        except ClientError as e:
            logger.error(f"S3 deletion failed: {e}")
            raise
