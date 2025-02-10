from fastapi import FastAPI, HTTPException
from pytezos import pytezos
import os

app = FastAPI()

# Configuration PyTezos avec Ghostnet
pytezos_client = pytezos.using(
    key=os.getenv("PRIVATE_KEY"),  # Stocke ta clé privée en variable d'env
    shell="https://ghostnet.ecadinfra.com"
)

USER_CONTRACT_ADDRESS = "KT1GFJgQGQUZzEuyqBrd8U9mCjqPRwhnzw2e"
TWEET_CONTRACT_ADDRESS = "KT1RtUit2h4cWm5hXgxc8DQcJkB1XctYHVdr"

@app.post("/create_user")
def create_user(username: str, bio: str):
    try:
        contract = pytezos_client.contract(USER_CONTRACT_ADDRESS)
        op = contract.create_user(username, bio).send()
        return {"message": "User created", "operation_hash": op.hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/post_tweet")
def post_tweet(content: str):
    try:
        contract = pytezos_client.contract(TWEET_CONTRACT_ADDRESS)
        op = contract.post_tweet(content).send()
        return {"message": "Tweet posted", "operation_hash": op.hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_tweets")
def get_tweets():
    try:
        contract = pytezos_client.contract(TWEET_CONTRACT_ADDRESS)
        tweets = contract.storage["tweets"]()
        return {"tweets": tweets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/delete_tweet")
def delete_tweet(tweet_id: int):
    try:
        contract = pytezos_client.contract(TWEET_CONTRACT_ADDRESS)
        op = contract.delete_tweet(tweet_id).send()
        return {"message": "Tweet deleted", "operation_hash": op.hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))