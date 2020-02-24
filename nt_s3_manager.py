import boto3


class NotetonS3Manager:
    def __init__(self, bucket_name='noteton', region_name='eu-central-1'):
        self.bucket = boto3.client('s3', region_name=region_name)
        self.bucket_name = bucket_name

    def put_image(self, user_id, list_id, item_id, obj):
        self.bucket.put_object(Bucket=self.bucket_name,
                               Body=obj,
                               Key=f'{user_id}/{list_id}/{item_id}.jpg')

    def get_image(self, user_id, list_id, item_id):
        self.bucket.get_object(Bucket=self.bucket_name,
                               Key=f'{user_id}/{list_id}/{item_id}.jpg')

    def get_list_images(self, user_id, list_id):
        objects = self.bucket.list_objects_v2(Bucket=self.bucket_name,
                                              Prefix=f'{user_id}/{list_id}')
        keys = [item['Key'] for item in objects['Contents']]

        return keys

    def generate_pre_signed_url(self, key):
        url = self.bucket.generate_presigned_url('get_object',
                                                 Params={
                                                    'Bucket': self.bucket_name,
                                                    'Key': key})
        return url
