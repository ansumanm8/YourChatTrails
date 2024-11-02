from fastapi.testclient import TestClient
from main import app

client = TestClient(app=app)

# Basic test script

test_id = None

def test_create_session():
    global test_id
    response = client.get('/api/v1/chat/create-new-conversation')
    data = response.json()
    sessionId = data.get('sessionId')
    assert response.status_code == 200
    assert response.json() == {"sessionId": sessionId}
    test_id = sessionId

def test_generate_response():
    response = client.post(f'/api/v1/chat/conversation/{test_id}?user_query=what is the issue here?')
    test_response = {
        "sessionId": test_id,
        "response": "we responded with something here!",
        "history": [
            "",
            "user: what is the issue here?",
            "bot: we responded with something here!"
        ]

    }
    assert response.status_code == 200
    assert response.json() == test_response


def test_delete_chat_session():
    response = client.delete(f'/api/v1/chat/delete-conversation/{test_id}')
    assert response.status_code == 200
    assert response.json() == {"message":"Session deleted successfully."}
