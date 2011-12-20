import bitcoin

connection = None

BITCOIN_HOST = '127.0.0.1'
BITCOIN_PORT = 8332
BITCOIN_USER = "test"
BITCOIN_PASS = "test"

from google.appengine.ext import db
class Settings(db.Expando):
    @classmethod
    def get_settings(cls, name='default'):
        s = cls.get_by_key_name(name)
        if not s:
            s = cls(key_name=name)
            s.put()
        return s

def reload_connection(user=None, password=None, host=None, port=None):
    global connection
    
    s = Settings.get_settings()
    s.BITCOIN_USER = user     or getattr(s, "BITCOIN_USER", None) or BITCOIN_USER
    s.BITCOIN_PASS = password or getattr(s, "BITCOIN_PASS", None) or BITCOIN_PASS
    s.BITCOIN_HOST = host     or getattr(s, "BITCOIN_HOST", None) or BITCOIN_HOST
    s.BITCOIN_PORT = port     or getattr(s, "BITCOIN_PORT", None) or BITCOIN_PORT
    s.put()    
    
    connection = bitcoin.connect_to_remote(
      s.BITCOIN_USER,
      s.BITCOIN_PASS,
      s.BITCOIN_HOST,
      port=s.BITCOIN_PORT,
    )
    
    print connection.proxy._ServiceProxy__serviceURL

reload_connection()
