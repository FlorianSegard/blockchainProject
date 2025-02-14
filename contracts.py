import smartpy as sp

@sp.module
def main():    
    # USERS
    class UserContract(sp.Contract):
        def __init__(self):
            self.data.DEPOSIT_AMOUNT = sp.tez(50)
            self.data.next_id = sp.nat(0)
            self.data.users = sp.big_map({})
            self.data.deposits = sp.big_map({})
            sp.cast(self.data.users, sp.big_map[sp.address, sp.record(
                id=sp.nat,
                username=sp.string,
                bio=sp.string,
                timestamp=sp.timestamp,
                deleted=sp.bool
            )])
            sp.cast(self.data.deposits, sp.big_map[sp.address, sp.mutez])

        @sp.entry_point
        def create_user(self, username, bio):
            assert len(username) <= 15, "USERNAME_TOO_LONG"
            assert len(bio) <= 150, "BIO_TOO_LONG"
            assert not self.data.users.contains(sp.sender) or self.data.users[sp.sender].deleted, "ALREADY_CREATED_USER"
            assert sp.amount >= self.data.DEPOSIT_AMOUNT, "INSUFFICIENT_DEPOSIT"
            
            self.data.users[sp.sender] = sp.record(
                id=self.data.next_id,
                username=username,
                bio=bio,
                timestamp=sp.now,
                deleted=False
            )
            self.data.deposits[sp.sender] = sp.amount
            self.data.next_id += 1

        @sp.entry_point
        def change_username(self, new_username):
            assert self.data.users.contains(sp.sender), "UNKNOWN_USER"
            assert len(new_username) <= 15, "USERNAME_TOO_LONG"
            
            self.data.users[sp.sender].username = new_username

        @sp.entry_point
        def change_bio(self, new_bio):
            assert self.data.users.contains(sp.sender), "UNKNOWN_USER"
            assert len(new_bio) <= 150, "BIO_TOO_LONG"
            
            self.data.users[sp.sender].bio = new_bio

        @sp.entry_point
        def delete_user(self):
            assert self.data.users.contains(sp.sender), "NO_USER_TO_DELETE"
            assert not self.data.users[sp.sender].deleted, "USER_ALREADY_DELETED"
            
            self.data.users[sp.sender].deleted = True
            sp.send(sp.sender, self.data.deposits[sp.sender])
            self.data.deposits[sp.sender] = sp.tez(0)

        @sp.entrypoint
        def default(self, user_address):
            assert self.data.users.contains(user_address) and not self.data.users[user_address].deleted, "USER_DOES_NOT_EXIST"

    # TWEETS
    class TweetContract(sp.Contract):
        def __init__(self, users_address):
            self.data.next_id = sp.nat(0)
            self.data.tweets = sp.big_map({})
            self.data.users_address = users_address
            sp.cast(self.data.tweets, sp.big_map[sp.nat, sp.record(
                author=sp.address,
                content=sp.string,
                timestamp=sp.timestamp,
                deleted=sp.bool
            )])

        @sp.entry_point
        def post_tweet(self, content):
            assert len(content) <= 280, "ERROR_TWEET_TOO_LONG"
            contract = sp.contract(sp.address, self.data.users_address, entrypoint="default").unwrap_some()
            sp.transfer(sp.sender, sp.mutez(0), contract)
            self.data.tweets[self.data.next_id] = sp.record(
                author=sp.sender,
                content=content,
                timestamp=sp.now,
                deleted=False
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

    c1.create_user(username="Pablito", bio="Hello, Glenn!", _sender=user1, _amount=sp.tez(20), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0), _valid=False, _exception="INSUFFICIENT_DEPOSIT")
    
    c1.create_user(username="Pablito", bio="Hello, Glenn!", _sender=user1, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c1.data.users[user1].username == "Pablito")
    scenario.verify(c1.data.users[user1].bio == "Hello, Glenn!")

    c1.create_user(username="CacaProut", bio="Hello again, Glenn", _sender=user2, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c1.data.users[user2].username == "CacaProut")

    long_bio = "A" * 151
    c1.create_user(username="MegaCaca", bio=long_bio, _sender=user1, _amount=sp.tez(50), _valid=False, _exception="BIO_TOO_LONG")

    c1.delete_user(_sender=user1)
    scenario.verify(c1.data.users[user1].deleted == True)

    c1.create_user(username="Pablito", bio="Hello, Glenn!", _sender=user1, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    c1.delete_user(_sender=user3, _valid=False, _exception="NO_USER_TO_DELETE")

    long_username = "A" * 16
    c1.create_user(username=long_username, bio="aaaaa", _sender=user3, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0), _valid=False, _exception="USERNAME_TOO_LONG")

    c1.change_username(long_username, _sender=user1, _valid=False, _exception="USERNAME_TOO_LONG")
    c1.change_bio(long_bio, _sender=user1, _valid=False, _exception="BIO_TOO_LONG")

    c1.change_username(long_username, _sender=user3, _valid=False, _exception="UNKNOWN_USER")
    c1.change_bio(long_bio, _sender=user3, _valid=False, _exception="UNKNOWN_USER")

    c1.change_username("MessoGlenn", _sender=user1)
    c1.change_bio("MessoGlennButItsTheBio", _sender=user1)
    scenario.verify(c1.data.users[user1].username == "MessoGlenn")
    scenario.verify(c1.data.users[user1].bio == "MessoGlennButItsTheBio")

    
    c2 = main.TweetContract(c1.address)
    scenario += c2
    c2.post_tweet("Hello, world!", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c2.data.tweets[0].author == user1)
    scenario.verify(c2.data.tweets[0].content == "Hello, world!")
    scenario.verify(c2.data.tweets[0].deleted == False)

    c2.delete_tweet(0, _sender=user1)
    scenario.verify(c2.data.tweets[0].deleted == True)
    c2.delete_tweet(1, _sender=user2, _valid=False, _exception="NO_TWEET_TO_DELETE")
