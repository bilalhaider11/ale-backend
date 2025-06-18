from common.app_logger import create_logger
from PIL import Image
from io import BytesIO
import requests
import base64

logger = create_logger()

def convert_image_to_png(source_data, source_type="url"):
    """
    Convert image to PNG format
    
    Args:
        source_data: Either URL string, base64 content, or raw bytes
        source_type: Either "url", "base64", or "bytes"
        
    Returns:
        tuple: (png_bytes, success) where png_bytes is the PNG image data as bytes
               and success is a boolean indicating if conversion was successful
    """
    try:
        logger.info(f"Converting image to PNG from {source_type}")
        
        # Get image data based on source type
        if source_type == "url":
            # Download image from URL
            response = requests.get(source_data, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
        elif source_type == "base64":
            # Decode base64 content
            image_data = base64.b64decode(source_data)
            
        elif source_type == "bytes":
            # Use raw bytes directly
            image_data = source_data
            
        else:
            logger.error(f"Unsupported source type: {source_type}")
            return None, False
        
        # Open image with PIL
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (PNG supports RGBA, but this ensures compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Keep transparency for RGBA and LA modes
            if image.mode == 'P':
                image = image.convert('RGBA')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to PNG
        png_buffer = BytesIO()
        image.save(png_buffer, format='PNG', optimize=True)
        png_bytes = png_buffer.getvalue()
        
        logger.info(f"Successfully converted image to PNG, size: {len(png_bytes)} bytes")
        return png_bytes, True
        
    except requests.RequestException as e:
        logger.error(f"Error downloading image from URL: {e}")
        return None, False
    except Exception as e:
        logger.exception(f"Error converting image to PNG: {e}")
        return None, False
