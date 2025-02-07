import smartpy as sp

@sp.module
def main():
    # USERS
    class UserContract(sp.Contract):
        def __init__(self):
            self.data.next_id=sp.nat(0)
            self.data.users=sp.big_map({})
            sp.cast(self.data.users, sp.big_map[sp.address, sp.record(
                    id=sp.nat,
                    username=sp.string,
                    bio=sp.string,
                    timestamp=sp.timestamp,
                    deleted=sp.bool)])

        @sp.entry_point
        def create_user(self, username, bio):
            assert len(bio) <= 150, "BIO_TOO_LONG"
            assert not self.data.users.contains(sp.sender), "ALREADY_CREATED_USER"
            self.data.users[sp.sender] = sp.record(
                id=self.data.next_id,
                username = username,
                bio = bio,
                timestamp = sp.now,
                deleted = False
            )
            self.data.next_id += 1

        @sp.entry_point
        def delete_user(self):
            assert self.data.users.contains(sp.sender), "NO_USER_TO_DELETE"
            self.data.users[sp.sender].deleted = True

    # TWEETS
    class TweetContract(sp.Contract):
        def __init__(self):
            self.data.next_id=sp.nat(0)
            self.data.tweets=sp.big_map({})
            sp.cast(self.data.tweets, sp.big_map[sp.nat, sp.record(
                    author=sp.address,
                    content=sp.string,
                    timestamp=sp.timestamp,
                    deleted=sp.bool)])
    
        @sp.entry_point
        def post_tweet(self, content):
            assert len(content) <= 280, "ERROR_TWEET_TOO_LONG"
            self.data.tweets[self.data.next_id] = sp.record(
                author = sp.sender,
                content = content,
                timestamp = sp.now,
                deleted = False
            )
            self.data.next_id += 1

        @sp.entry_point
        def delete_tweet(self, id):
            assert self.data.tweets.contains(id), "NO_TWEET_TO_DELETE"
            assert self.data.tweets[id].author == sp.sender, "NOT_RIGHT_PERSON"
            self.data.tweets[id].deleted = True

@sp.add_test()
def test():
    user1 = sp.address("tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb")
    user2 = sp.address("tz1aSkwEot3L2kmUvcoxzjMomb9mvBNuzFK6")
    user3 = sp.address("tz1afjrfnivoisnvdisubvospdncvr945dzd")
    
    scenario = sp.test_scenario("User Smart Contract", main)
    c1 = main.UserContract()
    scenario += c1
    
    c1.create_user(username = "Pablito", bio = "Hello, Glenn!", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c1.data.users[user1].username == "Pablito")
    scenario.verify(c1.data.users[user1].bio == "Hello, Glenn!")
    
    c1.create_user(username = "CacaProut", bio = "Hello again, Glenn", _sender=user2, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 5, 0))
    scenario.verify(c1.data.users[user2].username == "CacaProut")
    scenario.verify(c1.data.users[user2].bio == "Hello again, Glenn")
    
    long_bio = "A" * 151
    c1.create_user(username = "MegaCaca", bio = long_bio, _sender=user1, _valid=False, _exception="BIO_TOO_LONG")

    not_so_long_bio = "A" * 150
    c1.create_user(username = "MegaProut", bio = not_so_long_bio, _sender=user1, _valid=False, _exception="ALREADY_CREATED_USER")

    c1.delete_user(_sender=user1)
    scenario.verify(c1.data.users[user1].username == "Pablito")
    scenario.verify(c1.data.users[user1].deleted == True)

    c1.delete_user(_sender=user3, _valid=False, _exception="NO_USER_TO_DELETE")


    c2 = main.TweetContract()
    scenario += c2
    
    c2.post_tweet("Hello, world!", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 10, 0))
    scenario.verify(c2.data.tweets[0].author == user1)
    scenario.verify(c2.data.tweets[0].content == "Hello, world!")
    scenario.verify(c2.data.tweets[0].deleted == False)
    
    c2.post_tweet("Another day, another tweet.", _sender=user2, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 15, 0))
    scenario.verify(c2.data.tweets[1].author == user2)
    scenario.verify(c2.data.tweets[1].content == "Another day, another tweet.")
    
    long_tweet = "A" * 281
    c2.post_tweet(long_tweet, _sender=user1, _valid=False, _exception="ERROR_TWEET_TOO_LONG")
    
    c2.delete_tweet(0, _sender=user1)
    scenario.verify(c2.data.tweets[0].deleted == True)
        
    c2.delete_tweet(1, _sender=user1, _valid=False, _exception="NOT_RIGHT_PERSON")
    
    c2.delete_tweet(1, _sender=user2)
    scenario.verify(c2.data.tweets[1].deleted == True)
