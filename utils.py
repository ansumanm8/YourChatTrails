import uuid

# Set to store used UUIDs
used_uuids = set()

def generate_unique_uuid():
    while True:
        new_uuid = uuid.uuid4()  # Generate a new UUID
        if new_uuid not in used_uuids:
            used_uuids.add(new_uuid)  # Add it to the set
            return new_uuid
        

def generate_response(
        user_query: str,
        chat_history: list
    )-> str:
    """
        Generates final response based on the given user query and previous history.

        Args:

    """
    # Your Logic
    response = "we responded with something here!"
    return response
        