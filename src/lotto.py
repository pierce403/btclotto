import cgi

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import taskqueue, memcache

import btc
import logging
import random
import time
import os

class Tickets(db.Model):
  name    = db.StringProperty()
  inaddr  = db.StringProperty()
  outaddr = db.StringProperty()
  weight  = db.FloatProperty(default=0.0)
  spent   = db.FloatProperty(default=0.0)
  ctime   = db.DateTimeProperty(auto_now_add=True)
  mtime   = db.DateTimeProperty(auto_now=True)

class MainPage(webapp.RequestHandler):
  def get(self):
    os.environ['TZ'] = 'UTC'
    time.tzset()
    self.response.out.write('''
<html><body><center><br><br><br><small>
<form name="input" action="/" method="post">
1337 handle: <input type="text" name="name" /><br>
btc address: <input type="text" name="address" /><br>
<input type="submit" value="submit" />
</form>

1. enter your name and where you want to get paid<br>
2. you will be shown a funding address, send to it<br>
3. each day a random winner gets the pot<br>

<script language="JavaScript">
TargetDate = "'''+time.strftime("%m/%d/%Y")+''' 11:59:59 PM GMT";
BackColor = "white";
ForeColor = "black";
CountActive = true;
CountStepper = -1;
LeadingZero = true;
DisplayFormat = "%%H%% Hours, %%M%% Minutes, %%S%% Seconds.";
FinishMessage = "winner decided!";
</script>
<script src="countdown.js"></script>
<br><br>
''')
    lastwin = memcache.get("last_win")
    if lastwin is not None:
      lastwin = lastwin.replace('&',' ').replace('<',' ').replace('>',' ').replace('"',' ').replace("'",' ')  
      self.response.out.write("the last winner was "+lastwin+"!<br><br>")
 
    total = 0.0
    q=Tickets.all()
    q.order("-weight")
    q.filter("weight >",0.0);
    for t in q.fetch(100):
      total+=t.weight
      self.response.out.write(t.name[:12].replace('&',' ').replace('<',' ').replace('>',' ').replace('"',' ').replace("'",' ')+" "+str(t.weight)+" btc<br>\n")
    self.response.out.write("<br>total is "+str(total)+" btc")

  def post(self):
    self.response.out.write('<html><body><center><br><br><br>')

    outaddr=self.request.get('address')
    name=self.request.get('name')

    # make sure address looks right
    #try:
    #  btc.connection.sendtoaddress(outaddr,0.00000001)
    #
    #except Exception, e:
    #  logging.error(e)  
    #  logging.error(e.args)  
    #  self.response.out.write('btc address verification failed')
    #  return

    # get new address from server
    inaddr=btc.connection.getnewaddress()
    self.response.out.write("<br>to fund your entry, send some coins to")
    self.response.out.write("<br>"+inaddr)
    self.response.out.write("<br><br>this address will not be repeated")
    self.response.out.write("<br><br>remember, this is bitcoin, so it ")
    self.response.out.write("<br>may take 10 mins or so to show up")

    # add new ticket to database
    t = Tickets(name=name, inaddr=inaddr, outaddr=outaddr,weight=float(0.0))
    t.put()
    # log addition of new ticket

class DeclareWinner(webapp.RequestHandler):
  def get(self):

    total=0.0
    q=Tickets.all()
    q.order("-weight")
    q.filter("weight >",0);
    for t in q.fetch(100):
      total+=t.weight

    # generate random number
    winpoint=random.uniform(0,total)
    logging.info("winpoint is "+str(winpoint))
    self.response.out.write("winpoint is "+str(winpoint)+"<br>")

    # start looping until winpoint is less than zero
    q=Tickets.all()
    q.order("-weight")
    q.filter("weight >",0);
    for t in q.fetch(100):
      winpoint -= t.weight # are we below zero yet?
      logging.info(t.name + " has a winpoint of " + winpoint)
      t.spent  += t.weight # keep track of how many coins total have
      t.weight  = 0.0      #  been sent to this address
      t.put()
      if winpoint < 0.0 :
        winner = t.outaddr
        try :
          logging.info(t.name+" got "+str(total)+" coins")
          self.response.out.write(t.name+" got "+str(total)+" coins")
          btc.connection.sendtoaddress(winner,total)
          winpoint += total # make sure no one else can win
          memcache.set("last_win",t.name)
          continue
        except :
          # lame, the address was invalid
          t.delete()
          continue

    # delete old entries in database

class NewTransactions(webapp.RequestHandler):
  def get(self):

    # only check for new transactions if the balance has changed
    last_balance = memcache.get("last_balance")
    current_balance = btc.connection.getbalance()
    if last_balance == current_balance:
      logging.info("cool, the balance is the same "+str(current_balance))
      self.response.out.write("the balance is the same!")
      return

    memcache.set("last_balance",current_balance)

    # for each ticket in database
    q=Tickets.all()
    q.order("-mtime")
    for t in q.fetch(100) :
      total = btc.connection.getreceivedbyaddress(t.inaddr)
      if t.spent < total :
        # add updates to this round's weight
        t.weight = total - t.spent
        self.response.out.write(str(total)+" - "+str(t.spent)+"<br>")
        t.put()

application = webapp.WSGIApplication([('/',MainPage),('/winner',DeclareWinner),('/new',NewTransactions)])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
