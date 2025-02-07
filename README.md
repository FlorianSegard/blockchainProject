# Decentralized Twitter on Blockchain

## Overview
This project is a decentralized version of Twitter built on a blockchain. It allows users to create accounts and post tweets, ensuring transparency, security, and immutability through smart contracts.

## Features
- **User Registration:** Users can create accounts with a username and bio.
- **Tweet Posting:** Registered users can post tweets (up to 280 characters).
- **Data Storage:** Users and tweets are stored securely on the blockchain using smart contracts.
- **Account and Tweet Management:** Users can delete their accounts and tweets if needed.

## Smart Contracts
### 1. **UserContract**
- Manages user registrations and stores user profiles in a big map.
- Prevents duplicate accounts by mapping addresses to user IDs.

### 2. **TweetContract**
- Stores tweets and links them to users via user IDs.
- Ensures only registered users can post tweets.
- Supports tweet deletion by the author.

## Deployment
- The contracts can be deployed on any blockchain supporting SmartPy (e.g., Ghostnet or other test networks).
- Ensure both contracts are deployed, and the `TweetContract` is initialized with the `UserContract` address.

## Future Improvements
- **Likes & Retweets:** Implement reactions and retweets for user engagement.
- **User Mentions:** Allow tagging users in tweets.
- **NFT Tweets:** Optionally mint tweets as NFTs for uniqueness and ownership.

## Getting Started
1. Deploy `UserContract` to the blockchain.
2. Deploy `TweetContract` and link it to `UserContract`.
3. Interact with the contracts using SmartPy tools or blockchain explorers.

This project is an open-source experiment in decentralized social media. Feel free to contribute and improve it!

