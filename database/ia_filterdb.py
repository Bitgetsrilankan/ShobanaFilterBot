import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize MongoDB client and instance
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

# Define the Media document schema
@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')  # Primary key
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )  # Index on file_name for efficient searches
        collection_name = COLLECTION_NAME

# Function to save a media file to the database
async def save_file(media):
    """Save file in database"""
    # Unpack the file ID to get file_id and file_ref
    file_id, file_ref = unpack_new_file_id(media.file_id)
    # Clean up file name by replacing special characters with spaces
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    
    try:
        # Create a Media document instance
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2  # Validation error
    else:
        try:
            # Save the document to the database
            await file.commit()
        except DuplicateKeyError:
            logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in database')
            return False, 0  # Duplicate file
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1  # Success

# Function to search for media files based on a query
async def get_search_results(query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset, total_results)"""
    query = query.strip()
    
    # Build regex pattern for search
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return [], '', 0  # Invalid regex pattern

    # Define search filter
    if USE_CAPTION_FILTER:
        filter_dict = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter_dict = {'file_name': regex}
    
    if file_type:
        filter_dict['file_type'] = file_type

    # Get total number of matching documents
    total_results = await Media.count_documents(filter_dict)
    # Calculate next offset for pagination
    next_offset = offset + max_results if offset + max_results < total_results else ''
    
    # Query the database with sorting, skipping, and limiting
    cursor = Media.find(filter_dict).sort('$natural', -1).skip(offset).limit(max_results)
    files = await cursor.to_list(length=max_results)
    
    return files, next_offset, total_results

# Function to get details of a specific file by file_id
async def get_file_details(query):
    """Retrieve file details by file_id"""
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails

# Helper function to encode file ID
def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    # Append sentinel bytes [22, 4] to the input
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1  # Count consecutive zeros
        else:
            if n:
                r += b"\x00" + bytes([n])  # Encode zero runs
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

# Helper function to encode file reference
def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

# Helper function to unpack a new file ID
def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref