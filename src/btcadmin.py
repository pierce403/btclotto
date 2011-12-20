import cgi

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import taskqueue

import btc
import memcache
#import bitcoin
#import settings


class AdminPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('<html><body><center><br><br><br><small>')

        try:
            self.response.out.write('connection : '+btc.connection.proxy._ServiceProxy__serviceURL)
            self.response.out.write('<br>')
        except:
            self.response.out.write('no connection data<br>')

        try:
            btc.reload_connection()
            balance=btc.connection.getbalance()
            self.response.out.write('current balance : ')
            self.response.out.write(balance)
        except:
            self.response.out.write('could not connect to server');

        self.response.out.write('<br>')

        csrf="fixmelol!"
        self.response.out.write('''
            <form action="/btcadmin" method="post">
                <center>
                    <br><br><br>
                    <div>user<input type="text" name='user'></div>
                    <div>pass<input type="text" name='pass'></div>
                    <div>host<input type="text" name='host'></div>
                    <div>port<input type="text" name='port'></div>
                    <div>csrf<input type="hidden" ="'''+csrf+'''"></div>
                    <div><input type="submit" value="set connection"></div>
                </center>
            </form>''')
    def post(self):
        total="nothing"
        try:
            btc.reload_connection(
                self.request.get('user'),
                self.request.get('pass'),
                self.request.get('host'),
                self.request.get('port'))
            total=btc.connection.getbalance()
        except Exception, e:
            self.response.out.write('fail<pre>')
            self.response.out.write(total)
            self.response.out.write('\n')
            self.response.out.write(e)
            return

        self.response.out.write('win<pre>')
        self.response.out.write(total)

application = webapp.WSGIApplication([('/btcadmin',AdminPage)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
