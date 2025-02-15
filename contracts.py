import smartpy as sp

@sp.module
def main():    
    # USERS
    class UserContract(sp.Contract):
        def __init__(self,oracle_address):
            self.data.DEPOSIT_AMOUNT = sp.tez(50)
            self.data.oracle_address = oracle_address
            self.data.next_id = sp.nat(0)
            self.data.users = sp.big_map({})
            self.data.deposits = sp.big_map({})
            sp.cast(self.data.users, sp.big_map[sp.address, sp.record(
                id=sp.nat,
                username=sp.string,
                bio=sp.string,
                timestamp=sp.timestamp,
                last_username_change=sp.timestamp,
                last_bio_change=sp.timestamp,
                deleted=sp.bool,
                banned=sp.bool
            )])
            sp.cast(self.data.deposits, sp.big_map[sp.address, sp.mutez])

        @sp.entry_point
        def create_user(self, username, bio):
            assert len(username) <= 15, "USERNAME_TOO_LONG"
            assert len(bio) <= 150, "BIO_TOO_LONG"
            assert not self.data.users.contains(sp.sender) or self.data.users[sp.sender].deleted, "ALREADY_CREATED_USER"
            assert not self.data.users.contains(sp.sender) or not self.data.users[sp.sender].banned, "USER_IS_BANNED"
            assert sp.amount >= self.data.DEPOSIT_AMOUNT, "INSUFFICIENT_DEPOSIT"
            if not self.data.users.contains(sp.sender):
                oracle_contract = sp.contract(sp.address,self.data.oracle_address,entrypoint="request_bot_checking").unwrap_some()
                sp.transfer(sp.sender,sp.mutez(0),oracle_contract)

            self.data.users[sp.sender] = sp.record(
                id=self.data.next_id,
                username=username,
                bio=bio,
                timestamp=sp.now,
                last_username_change=sp.now,
                last_bio_change=sp.now,
                deleted=False,
                banned= False
            )
            self.data.deposits[sp.sender] = sp.amount
            self.data.next_id += 1

        @sp.entry_point
        def change_username(self, new_username):
            assert self.data.users.contains(sp.sender), "UNKNOWN_USER"
            assert not self.data.users[sp.sender].deleted, "DELETED_USER"
            assert sp.now - self.data.users[sp.sender].last_username_change > 24*60*60, "USERNAME_CHANGE_TOO_FREQUENT"
            assert len(new_username) <= 15, "USERNAME_TOO_LONG"

            self.data.users[sp.sender].username = new_username

        @sp.entry_point
        def change_bio(self, new_bio):
            assert self.data.users.contains(sp.sender), "UNKNOWN_USER"
            assert not self.data.users[sp.sender].deleted, "DELETED_USER"
            assert sp.now - self.data.users[sp.sender].last_bio_change > 4*60*60, "BIO_CHANGE_TOO_FREQUENT"
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
        def verified(self, user_address):
            assert self.data.users.contains(user_address) and not self.data.users[user_address].deleted, "USER_DOES_NOT_EXIST"
            #TODO check  data and banned and assert ban
            is_user_botting_opt = sp.view("get_is_botting",self.data.oracle_address,(user_address,sp.self_address()),sp.option[sp.bool]).unwrap_some()
            if is_user_botting_opt.is_some():
                is_user_botting = is_user_botting_opt.unwrap_some()
                if is_user_botting:
                    self.data.users[user_address].banned = True
                    self.data.users[user_address].deleted = True

        @sp.entrypoint
        def default(self):
            pass

    # TWEETS
    class TweetContract(sp.Contract):
        def __init__(self, users_address):
            self.data.next_id = sp.nat(0)
            self.data.tweets = sp.big_map({})
            self.data.users_address = users_address
            self.data.last_tweet_time = sp.big_map({})
            sp.cast(self.data.tweets, sp.big_map[sp.nat, sp.record(
                author=sp.address,
                content=sp.string,
                timestamp=sp.timestamp,
                deleted=sp.bool
            )])

        @sp.entry_point
        def post_tweet(self, content):
            assert len(content) <= 280, "ERROR_TWEET_TOO_LONG"
            if self.data.last_tweet_time.contains(sp.sender):
                assert sp.now - self.data.last_tweet_time[sp.sender] > 60, "TOO_MANY_TWEETS_TOO_FAST"
            contract = sp.contract(sp.address, self.data.users_address, entrypoint="verified").unwrap_some()
            sp.transfer(sp.sender, sp.mutez(0), contract)
            self.data.tweets[self.data.next_id] = sp.record(
                author=sp.sender,
                content=content,
                timestamp=sp.now,
                deleted=False
            )
            self.data.last_tweet_time[sp.sender] = sp.now
            self.data.next_id += 1

        @sp.entry_point
        def delete_tweet(self, id):
            assert self.data.tweets.contains(id) and not self.data.tweets[id].deleted, "NO_TWEET_TO_DELETE"
            assert self.data.tweets[id].author == sp.sender, "NOT_RIGHT_PERSON"
            self.data.tweets[id].deleted = True


    #Oracle
    class BotFindingOracle(sp.Contract):
        def __init__(self,source_public_key):
            self.data.requests = sp.big_map({})
            self.data.source_public_key = source_public_key

        @sp.entrypoint
        def request_bot_checking(self,address_of_checked):
            sp.cast(address_of_checked,sp.address)
            key = (address_of_checked,sp.sender)
            assert not self.data.requests.contains(key), "request exists already"
            self.data.requests[key]=sp.record(address_of_checked = address_of_checked,result = None)

        @sp.entrypoint
        def receive_result(self,address_of_checked,sender,message,signature):
            sp.cast(message,sp.record(address_of_checked = sp.address,result = sp.bool))
            key = (address_of_checked,sender)
            assert sp.check_signature(self.data.source_public_key,signature,sp.pack(message))
            assert self.data.requests[key].result == None, "result already received"
            self.data.requests[key].result = sp.Some(message.result)

        @sp.onchain_view()
        def get_is_botting(self,key):
            sp.cast(key,sp.pair[sp.address,sp.address])
            return self.data.requests[key].result



@sp.add_test()
def test():
    user1 = sp.address("tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb")
    user2 = sp.address("tz1aSkwEot3L2kmUvcoxzjMomb9mvBNuzFK6")
    user3 = sp.address("tz1afjrfnivoisnvdisubvospdncvr945dzd")
    bot1_sim = sp.test_account("Bot1")
    bot1 = bot1_sim.address
    source = sp.test_account("Test_source")
    scenario = sp.test_scenario("User Smart Contract", main)
    contract_oracle = main.BotFindingOracle(source.public_key)
    c1 = main.UserContract(contract_oracle.address)
    scenario += c1
    scenario += contract_oracle

    c1.create_user(username="Pablito", bio="Hello, Glenn!", _sender=user1, _amount=sp.tez(20), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0), _valid=False, _exception="INSUFFICIENT_DEPOSIT")

    c1.create_user(username="Pablito", bio="Hello, Glenn!", _sender=user1, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c1.data.users[user1].username == "Pablito")
    scenario.verify(c1.data.users[user1].bio == "Hello, Glenn!")

    c1.create_user(username="Carlito", bio="Hello again, Glenn", _sender=user2, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c1.data.users[user2].username == "Carlito")

    long_bio = "A" * 151
    c1.create_user(username="Marlito", bio=long_bio, _sender=user1, _amount=sp.tez(50), _valid=False, _exception="BIO_TOO_LONG")

    c1.delete_user(_sender=user1)
    scenario.verify(c1.data.users[user1].deleted == True)

    c1.create_user(username="botter800", bio="I will spam everything", _sender=bot1, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    c1.create_user(username="Pablito", bio="Hello, Glenn!", _sender=user1, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    c1.delete_user(_sender=user3, _valid=False, _exception="NO_USER_TO_DELETE")

    long_username = "A" * 16
    c1.create_user(username=long_username, bio="aaaaa", _sender=user3, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0), _valid=False, _exception="USERNAME_TOO_LONG")

    c1.change_username(long_username, _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 8, 12, 0, 1), _valid=False, _exception="USERNAME_TOO_LONG")
    c1.change_bio(long_bio, _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 8, 16, 0, 1), _valid=False, _exception="BIO_TOO_LONG")

    c1.change_username(long_username, _now=sp.timestamp_from_utc(2025, 2, 8, 12, 0, 1), _sender=user3, _valid=False, _exception="UNKNOWN_USER")
    c1.change_bio(long_bio, _sender=user3, _now=sp.timestamp_from_utc(2025, 2, 7, 16, 0, 1), _valid=False, _exception="UNKNOWN_USER")

    c1.change_username("MessoGlenn", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 8, 12, 0, 0), _valid=False, _exception="USERNAME_CHANGE_TOO_FREQUENT")
    c1.change_bio("MessoGlennButItsTheBio", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 16, 0, 0), _valid=False, _exception="BIO_CHANGE_TOO_FREQUENT")

    c1.change_username("MessoGlenn", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 8, 12, 0, 1))
    c1.change_bio("MessoGlennButItsTheBio", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 16, 0, 1))
    scenario.verify(c1.data.users[user1].username == "MessoGlenn")
    scenario.verify(c1.data.users[user1].bio == "MessoGlennButItsTheBio")


    c2 = main.TweetContract(c1.address)
    scenario += c2
    c2.post_tweet("Hello, world!", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0))
    scenario.verify(c2.data.tweets[0].author == user1)
    scenario.verify(c2.data.tweets[0].content == "Hello, world!")
    scenario.verify(c2.data.tweets[0].deleted == False)

    c2.post_tweet("Hello!", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0), _valid=False, _exception="TOO_MANY_TWEETS_TOO_FAST")
    c2.post_tweet("world", _sender=user1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 1, 1))

    message1 = sp.record(address_of_checked = user2, result = False)
    signature1 = sp.make_signature(source.secret_key,sp.pack(message1))
    contract_oracle.receive_result(address_of_checked = user2,
                                  sender = c1.address,
                                  message = message1,
                                  signature = signature1)
    message2= sp.record(address_of_checked = bot1, result = True)
    signature2 = sp.make_signature(source.secret_key,sp.pack(message2))
    contract_oracle.receive_result(address_of_checked = bot1,
                                  sender = c1.address,
                                  message = message2,
                                  signature = signature2)

    c2.post_tweet("Another day, another tweet.", _sender=user2, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 15, 0))
    scenario.verify(c2.data.tweets[2].author == user2)
    c2.post_tweet("Another day, another tweet.", _sender=bot1, _now=sp.timestamp_from_utc(2025, 2, 7, 12, 15, 0))

    c2.post_tweet("Another day, another tweet.", _sender=bot1, _now=sp.timestamp_from_utc(2025, 2, 8, 12, 15, 0),_valid=False, _exception="USER_DOES_NOT_EXIST")
    scenario.verify(c2.data.tweets[2].content == "Another day, another tweet.")
    c1.change_username("MessoGlenn", _sender=bot1, _now=sp.timestamp_from_utc(2025, 2, 8, 12, 0, 1),_valid=False,_exception="DELETED_USER")
    c1.create_user(username="Guess who's bac", bio="aaaaa", _sender=bot1, _amount=sp.tez(50), _now=sp.timestamp_from_utc(2025, 2, 7, 12, 0, 0), _valid=False, _exception="USER_IS_BANNED")
    long_tweet = "A" * 281
    c2.post_tweet(long_tweet, _sender=user1, _valid=False, _exception="ERROR_TWEET_TOO_LONG")

    c2.post_tweet("AAAA", _sender=user3, _valid=False, _exception="USER_DOES_NOT_EXIST")


    c2.delete_tweet(0, _sender=user1)
    scenario.verify(c2.data.tweets[0].deleted == True)
    c2.delete_tweet(0, _sender=user1, _valid=False, _exception="NO_TWEET_TO_DELETE")
    c2.delete_tweet(0, _sender=user2, _valid=False, _exception="NO_TWEET_TO_DELETE")

    c2.delete_tweet(2, _sender=user1, _valid=False, _exception="NOT_RIGHT_PERSON")

    c2.delete_tweet(2, _sender=user2)
    scenario.verify(c2.data.tweets[2].deleted == True)
