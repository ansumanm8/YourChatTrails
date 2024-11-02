from fastapi import FastAPI, HTTPException, status, Request
from utils import generate_unique_uuid, generate_response
from models import GenerateResponse
from dotenv import load_dotenv
import redis
import time
import os

# Loading environment variables
load_dotenv()

# Setting up redis client
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"), 
    port=os.getenv("REDIS_PORT"), 
    db=os.getenv("REDIS_DB"), 
    decode_responses=True
    )


app = FastAPI(
    title="YourChatTrails",
    root_path="/api/v1"
)

CHAT_SESSION_STORE_PATH = './chat-session-store'


@app.on_event("startup")
async def startup_event():
    try:
        redis_client.ping()
        print("Connected to Redis server.")
    except redis.ConnectionError():
        raise Exception("Redis server is not reachable. Please start the Redis server.")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get('/')
async def Your_Chat_Trails():
    """
    Welcome function!
    """
    return {"message": "YourChatTrails server up and running"}


@app.get('/chat/create-new-conversation')
async def create_new_conversation()->dict:
    """
    Creates a new chat session for the specified user in Redis and stores the session data. 
    Session data will be stored for 15 days. 

    Returns:
        str: The unique session ID for the created chat session.
        
    Raises:
        Exception: If there is an error while creating the session data in Redis.
    """

    # Generating new sessionId
    new_session_id = f"{generate_unique_uuid()}:messages"

    try:
        # Creates a new list in Redis with a empty element
        redis_client.rpush(new_session_id, "")

        # Setting up time to live
        ttl_seconds = 15 * 24 * 60 * 60
        redis_client.expire(new_session_id, ttl_seconds)

        return {
            "sessionId": new_session_id
        }
    except Exception as e:
        print('Error - ', e)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

  
@app.post('/chat/conversation/{sessionId}', response_model=GenerateResponse)
async def generate_chat_response(sessionId: str, user_query: str)-> dict:
    """
    Generates a response based on the provided user query and logs it to a session file.

    Args:
        user_query (str): The query provided by the user that requires a response.
        session_file (str): The path to the session file where the response will be recorded.
        
    Returns:
        str: The generated response based on the user query.

    Raises:
        Exception: If there is an error writing to the redis session.
        
    """
    
    if not redis_client.exists(sessionId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session ID not found!"
        )
    
    try:
        # Inserting question into DB
        redis_client.rpush(sessionId, f"user: {user_query}")

        # Response Generation Logic
        response = generate_response(
            user_query=user_query,
            chat_history=redis_client.lrange(sessionId, 0, -1)
        )
        
        # Inserting response into DB
        redis_client.rpush(sessionId,f"bot: {response}")

        history = redis_client.lrange(sessionId, 0, -1)
        return {
            "sessionId": sessionId,
            "response": response,
            "history": history
        }
    except Exception as e:
        print(f'Error - {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while generating response"
        )
    
@app.delete('/chat/delete-conversation/{sessionId}',
            responses={200: {"message": "Session deleted successfully."},
                       500: {"message":"Something went wrong."}})
async def delete_conversation(sessionId)->dict:
    """
    Deletes the chat session for the specified user when they exit the interface.

    Args:
        user_id (str): The unique identifier for the user whose chat session is to be deleted.

    Returns:
        str: This function returns a success message.

    Raises:
        ConnectionError: If the Redis connection is not reachable.
        KeyError: If the user ID does not exist in the session store.
    """
    if redis_client.exists(sessionId):
        try:
            redis_client.delete(sessionId)
            return {
                "message": "Session deleted successfully."
            }
        except redis.ConnectionError():
            raise Exception("Redis server error.")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session Not Found."
        )



# TODO:
# Expiration renewal logic - design