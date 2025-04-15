
def process_message(message):                                                                                                                            
    """Process the message to handle file operations."""                                                                                                 
    s3_key = message.get('s3_key')                                                                                                                       
    if not s3_key:                                                                                                                                       
        raise ValueError("No s3_key found in message")                                                                                                   
                                                                                                                                                         
    # Implement the logic to download and process the file                                                                                               
    # For example, use S3ClientService to download the file                                                                                              
    # and then perform any necessary processing                                                                                                          
    print(f"Processing file with s3_key: {s3_key}") 