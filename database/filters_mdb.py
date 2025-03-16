import pymongo
from pyrogram import enums
from info import DATABASE_URI, DATABASE_NAME, DATABASE_NAME2
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Connect to MongoDB
myclient = pymongo.MongoClient(DATABASE_URI)
mydb1 = myclient[DATABASE_NAME]    # First database
mydb2 = myclient[DATABASE_NAME2]   # Second database

# Function to choose the database based on group_id
def get_db_for_group(grp_id):
    """
    Determines which database to use based on the group_id.
    Even group_ids use mydb2, odd group_ids use mydb1.
    """
    if int(grp_id) % 2 == 0:
        return mydb2  # Even group_ids use second database
    else:
        return mydb1  # Odd group_ids use first database

# Add a filter to the appropriate database
async def add_filter(grp_id, text, reply_text, btn, file, alert):
    """
    Adds or updates a filter in the database selected by group_id.
    
    Args:
        grp_id: Group ID to determine the database
        text: Filter trigger text
        reply_text: Reply message for the filter
        btn: Button data
        file: File ID
        alert: Alert message
    """
    mydb = get_db_for_group(grp_id)
    mycol = mydb[str(grp_id)]
    
    data = {
        'text': str(text),
        'reply': str(reply_text),
        'btn': str(btn),
        'file': str(file),
        'alert': str(alert)
    }

    try:
        mycol.update_one({'text': str(text)}, {"$set": data}, upsert=True)
    except Exception as e:
        logger.exception('Error adding filter!', exc_info=True)

# Find a filter in the appropriate database
async def find_filter(group_id, name):
    """
    Finds a filter by name in the database selected by group_id.
    
    Returns:
        Tuple of (reply_text, btn, alert, fileid) or (None, None, None, None) if not found
    """
    mydb = get_db_for_group(group_id)
    mycol = mydb[str(group_id)]
    
    query = mycol.find({"text": name})
    try:
        for file in query:
            reply_text = file['reply']
            btn = file['btn']
            fileid = file['file']
            alert = file.get('alert')  # Use .get() to handle missing 'alert' key
            return reply_text, btn, alert, fileid
    except Exception:
        pass
    return None, None, None, None

# Get all filters from the appropriate database
async def get_filters(group_id):
    """
    Retrieves all filter trigger texts for a group from its database.
    
    Returns:
        List of filter texts
    """
    mydb = get_db_for_group(group_id)
    mycol = mydb[str(group_id)]

    texts = []
    query = mycol.find()
    try:
        for file in query:
            text = file['text']
            texts.append(text)
    except Exception:
        pass
    return texts

# Delete a specific filter from the appropriate database
async def delete_filter(message, text, group_id):
    """
    Deletes a filter by text from the database selected by group_id.
    
    Args:
        message: Pyrogram message object to reply to
        text: Filter text to delete
        group_id: Group ID to determine the database
    """
    mydb = get_db_for_group(group_id)
    mycol = mydb[str(group_id)]
    
    myquery = {'text': text}
    if mycol.count_documents(myquery) == 1:
        mycol.delete_one(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that filter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("Couldn't find that filter!", quote=True)

# Delete all filters from the appropriate database
async def del_all(message, group_id, title):
    """
    Deletes all filters for a group from its database.
    
    Args:
        message: Pyrogram message object to edit
        group_id: Group ID to determine the database
        title: Title or name of the group for the response
    """
    mydb = get_db_for_group(group_id)
    mycol = mydb[str(group_id)]
    try:
        mycol.drop()
        await message.edit_text(f"All filters from {title} have been removed")
    except Exception:
        await message.edit_text("Couldn't remove all filters from group!")

# Count filters in the appropriate database
async def count_filters(group_id):
    """
    Counts the number of filters in the database for a group.
    
    Returns:
        Number of filters, or False if none exist
    """
    mydb = get_db_for_group(group_id)
    mycol = mydb[str(group_id)]

    count = mycol.count_documents({})
    return False if count == 0 else count

# Get statistics from both databases
async def filter_stats():
    """
    Aggregates filter statistics across both databases.
    
    Returns:
        Tuple of (total number of groups, total number of filters)
    """
    collections1 = mydb1.list_collection_names()  # Collections in first database
    collections2 = mydb2.list_collection_names()  # Collections in second database

    # Remove unnecessary collections like "CONNECTION"
    for col_list in (collections1, collections2):
        if "CONNECTION" in col_list:
            col_list.remove("CONNECTION")

    totalcount = 0
    # Count from first database
    for collection in collections1:
        mycol = mydb1[collection]
        count = mycol.count_documents({})
        totalcount += count
    # Count from second database
    for collection in collections2:
        mycol = mydb2[collection]
        count = mycol.count_documents({})
        totalcount += count

    totalcollections = len(collections1) + len(collections2)
    return totalcollections, totalcount