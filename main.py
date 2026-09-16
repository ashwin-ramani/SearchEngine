from flask import Flask, render_template, request
from crawler import start_crawler
import json
import search

app = Flask(__name__)

@app.route("/")
def home():
  return render_template("home.html")

@app.route("/search")
def _search():
  return search.results(request.args["query"])

start_crawler()
app.run()
