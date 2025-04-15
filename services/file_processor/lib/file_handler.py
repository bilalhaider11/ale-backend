
def process_message(message):                                                                                                                            
    """Process the message to handle file operations."""                                                                                                 
    s3_key = message.get('s3_key')                                                                                                                       
    if not s3_key:                                                                                                                                       
        raise ValueError("No s3_key found in message")                                                                                                   
                                                                                                                                                         
    # Parse the S3 key to extract org_id and person_id
    parts = s3_key.strip('/').split('/')
    if len(parts) < 3:
        raise ValueError("Invalid s3_key format")

    org_id = parts[2]
    person_id = "system" if parts[1] == "system" else parts[3] if len(parts) > 3 else None

    if person_id is None:
        raise ValueError("Invalid s3_key format for user file")

    # Implement the logic to download and process the file
    # For example, use S3ClientService to download the file
    # and then perform any necessary processing
    print(f"Processing file for org_id: {org_id}, person_id: {person_id}")
    print(f"Processing file with s3_key: {s3_key}") 
