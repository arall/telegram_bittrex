from peewee import Field, Model, PrimaryKeyField, TextField, CharField, DateTimeField, IntegerField, DecimalField, BooleanField
from playhouse.db_url import connect
from secrets import DB
import datetime

db = connect(DB)

# this is not necessary, because peewee open the connection automatically
def before_execute_any_query():
    db.connect(DB)

# after execute all queries and complete the action
def after_execute_query():
    db.close(DB)

class Satoshi(DecimalField):
    def db_value(self, value):
        if value is not None:
            return '%.8f' % value


class Signal(Model):
    class Meta:
        database = db
        db_table = 'signals'

    id = PrimaryKeyField()

    # Signal data
    chat_id = CharField(null=True)
    username = CharField(null=True)
    text = TextField()
    auto = BooleanField(default=True)
    coin = CharField()
    market = CharField()
    win_percent = IntegerField(null=True)
    win_price = Satoshi(null=True, max_digits=40, decimal_places=8)
    stop_loss = Satoshi(null=True, max_digits=40, decimal_places=8)
    stop_loss_percent = IntegerField(null=True)
    date = DateTimeField(default=datetime.datetime.now)

    # Operation data
    quantity = Satoshi(null=True, max_digits=40, decimal_places=8)  # Amount of coin purshased
    btc = Satoshi(null=True, max_digits=40, decimal_places=8)       # Amount of BTCs used
    status = IntegerField()

    # Statistics
    current_price = Satoshi(null=True, max_digits=40, decimal_places=8)
    highest_price = Satoshi(null=True, max_digits=40, decimal_places=8)
    lowest_price = Satoshi(null=True, max_digits=40, decimal_places=8)

    # Post-Buy data
    b_uuid = CharField(null=True)
    b_comision = Satoshi(null=True, max_digits=40, decimal_places=8)
    b_price = Satoshi(null=True, max_digits=40, decimal_places=8)
    b_date = DateTimeField(null=True)

    # Post-Sell data
    s_uuid = CharField(null=True)
    s_comision = Satoshi(null=True, max_digits=40, decimal_places=8)
    s_price = Satoshi(null=True, max_digits=40, decimal_places=8)
    s_date = DateTimeField(null=True)

    # Analysis data
    profit_btc = Satoshi(null=True, max_digits=40, decimal_places=8)
    profit_percent = Satoshi(null=True, max_digits=40, decimal_places=8)


db.create_tables([Signal], safe=True)
