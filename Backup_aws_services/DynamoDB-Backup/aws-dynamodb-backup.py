import boto3
import json
import os
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Initialize DynamoDB client with the default session
session = boto3.Session()
dynamodb = session.client('dynamodb')

# Directory for backups
backup_dir = 'Backup_dynamodb_tables'
os.makedirs(backup_dir, exist_ok=True)

try:
    # Fetch all DynamoDB table names
    response = dynamodb.list_tables()
    table_names = response['TableNames']
    logger.info(f'Found {len(table_names)} tables to back up.')
    
    # Backup each table
    for table_name in table_names:
        logger.info(f'Starting backup for table: {table_name}')
        
        all_items = []
        last_evaluated_key = None

        # Perform paginated scan
        while True:
            try:
                scan_params = {'TableName': table_name}
                if last_evaluated_key:
                    scan_params['ExclusiveStartKey'] = last_evaluated_key

                response = dynamodb.scan(**scan_params)
                all_items.extend(response.get('Items', []))
                last_evaluated_key = response.get('LastEvaluatedKey')
                
                if not last_evaluated_key:
                    break
            except (BotoCoreError, ClientError) as error:
                logger.error(f'Error scanning table {table_name}: {error}')
                break
        
        # Save to JSON
        backup_file = os.path.join(backup_dir, f'{table_name}_backup.json')
        try:
            with open(backup_file, 'w') as outfile:
                json.dump(all_items, outfile, indent=4)
            logger.info(f'Backup successful for {table_name}, saved to {backup_file}')
        except IOError as io_error:
            logger.error(f'Failed to write backup for {table_name}: {io_error}')
            
except (BotoCoreError, ClientError) as error:
    logger.error(f'Failed to list tables: {error}')

logger.info('All table backups are completed!')
