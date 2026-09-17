import chromadb
import uuid
import os

# 1. Initialize persistent local storage in your project folder
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iris_memory")
chroma_client = chromadb.PersistentClient(path=db_path)

# 2. Create or load the "table" for the memories
collection = chroma_client.get_or_create_collection(name="user_knowledge")

def save_memory(fact: str) -> str:
    """
    Saves a fact, preference, or piece of information to long-term memory.
    Use this when the user explicitly asks you to remember something or save a fact.
    """
    print(f"[IRIS Memory] Saving new fact: {fact}")
    doc_id = str(uuid.uuid4())
    
    collection.add(
        documents=[fact],
        ids=[doc_id]
    )
    return f"Successfully saved to long-term memory: {fact}"

def search_memory(query: str) -> str:
    """
    Searches the user's long-term memory for relevant information.
    Use this when the user asks you to recall something, or asks a question about past facts.
    """
    print(f"[IRIS Memory] Searching for: {query}")
    
    # Prevent errors if the database is currently empty
    if collection.count() == 0:
        return "There is nothing saved in long-term memory yet."
        
    results = collection.query(
        query_texts=[query],
        n_results=2 # Retrieve the top 2 most mathematically similar memories
    )
    
    if results['documents'] and results['documents'][0]:
        memories = " | ".join(results['documents'][0])
        return f"Found relevant memories: {memories}"
        
    return "I could not find anything relevant in your memory banks."