import pymongo
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, DATABASE_URI2, DATABASE_NAME2, COLLECTION_NAME2
import logging

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Connect to the first database
myclient1 = pymongo.MongoClient(DATABASE_URI)
mydb1 = myclient1[DATABASE_NAME]
mycol1 = mydb1[COLLECTION_NAME]

# Connect to the second database
myclient2 = pymongo.MongoClient(DATABASE_URI2)
mydb2 = myclient2[DATABASE_NAME2]
mycol2 = mydb2[COLLECTION_NAME2]

# Functions are set up to work with both databases

async def add_connection(col, group_id, user_id):
    """Adds a new connection to the collection."""
    query = col.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0}
    )
    if query is not None:
        group_ids = [x["group_id"] for x in query["group_details"]]
        if group_id in group_ids:
            return False

    group_details = {"group_id": group_id}
    data = {
        '_id': user_id,
        'group_details': [group_details],
        'active_group': group_id,
    }

    if col.count_documents({"_id": user_id}) == 0:
        try:
            col.insert_one(data)
            return True
        except:
            logger.exception('Some error occurred!', exc_info=True)
    else:
        try:
            col.update_one(
                {'_id': user_id},
                {
                    "$push": {"group_details": group_details},
                    "$set": {"active_group": group_id}
                }
            )
            return True
        except:
            logger.exception('Some error occurred!', exc_info=True)

async def active_connection(col, user_id):
    """Retrieves the active group ID for the user."""
    query = col.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0}
    )
    if not query:
        return None
    group_id = query['active_group']
    return int(group_id) if group_id is not None else None

async def all_connections(col, user_id):
    """Retrieves all group IDs connected to the user."""
    query = col.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0}
    )
    if query is not None:
        return [x["group_id"] for x in query["group_details"]]
    return None

async def if_active(col, user_id, group_id):
    """Checks if the user's active group ID matches the given group_id."""
    query = col.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0}
    )
    return query is not None and query['active_group'] == group_id

async def make_active(col, user_id, group_id):
    """Sets the given group_id as active."""
    update = col.update_one(
        {'_id': user_id},
        {"$set": {"active_group": group_id}}
    )
    return update.modified_count != 0

async def make_inactive(col, user_id):
    """Sets the user's active group to inactive."""
    update = col.update_one(
        {'_id': user_id},
        {"$set": {"active_group": None}}
    )
    return update.modified_count != 0

async def delete_connection(col, user_id, group_id):
    """Removes a group_id from the user's connections."""
    try:
        update = col.update_one(
            {"_id": user_id},
            {"$pull": {"group_details": {"group_id": group_id}}}
        )
        if update.modified_count == 0:
            return False
        query = col.find_one(
            {"_id": user_id},
            {"_id": 0}
        )
        if len(query["group_details"]) >= 1:
            if query['active_group'] == group_id:
                prvs_group_id = query["group_details"][-1]["group_id"]
                col.update_one(
                    {'_id': user_id},
                    {"$set": {"active_group": prvs_group_id}}
                )
        else:
            col.update_one(
                {'_id': user_id},
                {"$set": {"active_group": None}}
            )
        return True
    except Exception as e:
        logger.exception(f'Some error occurred! {e}', exc_info=True)
        return False