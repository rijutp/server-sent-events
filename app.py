# author: oskar.blom@gmail.com
#
# Make sure your gevent version is >= 1.0
import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue

from flask import Flask, Response, render_template, request, url_for, redirect

import time


# SSE "protocol" is described here: http://mzl.la/UPFyxY
class ServerSentEvent(object):

    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) 
                 for k, v in self.desc_map.iteritems() if k]
        
        return "%s\n\n" % "\n".join(lines)

app = Flask(__name__)
subscriptions = []

# Client code consumes like this.
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin", methods=["GET","POST"])
def admin():
    return render_template("admin.html")

@app.route("/debug")
def debug():
    return "Currently %d subscriptions" % len(subscriptions)

@app.route("/publish")
def publish():
    #Dummy data - pick up from request for real data
    message = request.args.get('message')
    print message
    def notify():
        for sub in subscriptions[:]:
            sub.put(message)
    gevent.spawn(notify)
    
    return redirect(url_for('admin'))

@app.route("/subscribe")
def subscribe():
    def gen():
        q = Queue()
        subscriptions.append(q)
        try:
            while True:
                result = q.get()
                ev = ServerSentEvent(str(result))
                yield ev.encode()
        except GeneratorExit: # Or maybe use flask signals
            subscriptions.remove(q)

    return Response(gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.debug = True
    server = WSGIServer(("", 5000), app)
    server.serve_forever()
    # Then visit http://localhost:5000 to subscribe 
    # and send messages by visiting http://localhost:5000/publish
