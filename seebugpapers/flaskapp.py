# -*- coding: utf-8 -*-
import re
import os
import math
import pymongo
from flask import Flask, request, render_template, send_file, abort, redirect
# setting:
MONGODB_SERVER = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'seebugpaper'
MONGODB_COLLECTION = 'papers'
ROWS_PER_PAGE = 20

app = Flask(__name__, static_url_path="", static_folder='papersite')
app.config.from_object(__name__)
# monogodb connection string
connection_string = "mongodb://%s:%d" % (
    app.config['MONGODB_SERVER'], app.config['MONGODB_PORT'])


def get_search_regex(keywords, search_by_html):
    keywords_regex = {}
    kws = [ks for ks in keywords.strip().split(' ') if ks != '']
    field_name = 'html' if search_by_html else 'title'
    if len(kws) > 0:
        reg_pattern = re.compile('|'.join(kws), re.IGNORECASE)
        # keywords_regex[field_name]={'$regex':'|'.join(kws)}
        keywords_regex[field_name] = reg_pattern

    return keywords_regex

@app.route('/')
def index():
    contents = []
    page = request.args.get("page", '1')
    if not page.isdigit():
        page = 1
    page = int(page)
    search = request.args.get('keyword', "")
    row_start = (int(page) - 1)*30
    client = pymongo.MongoClient(connection_string)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    if search:
        keywords = get_search_regex(search, True)
        cursor = collection.find(keywords).sort(
            'date', pymongo.DESCENDING).skip(row_start).limit(30)
        pages = math.ceil(collection.find(keywords).count()/30)
    else:
        cursor = collection.find().sort('date', pymongo.DESCENDING).skip(row_start).limit(30)
        pages = math.ceil(collection.find().count()/30)
    for c in cursor:
        c["date"] = c["date"].strftime('%Y-%m-%d')
        contents.append(c)
    return render_template('index.html', page=page, pages=pages, contents=contents)


@app.route("/<int:pid>")
def pidhtml(pid):
    if os.path.exists("papersite/{}.html".format(pid)):
        return send_file("papersite/{}.html".format(pid))
    else:
        return abort(404)

@app.route("/<int:pid>/")
def redirectPid(pid):
    if os.path.exists("papersite/{}.html".format(pid)):
        return redirect("https://{}/{}".format(request.host ,pid),302)
    else:
        return abort(404)

@app.route("/category/<category>/")
def filterCategory(category):
    if '-' in category:
        kws = category.split('-')
        category = re.compile('|'.join(kws), re.IGNORECASE)
    contents = []
    page = request.args.get("page", '1')
    if not page.isdigit():
        page = 1
    page = int(page)
    row_start = (int(page) - 1)*30
    client = pymongo.MongoClient(connection_string)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    cursor = collection.find({"category_uri":category}).sort(
            'date', pymongo.DESCENDING).skip(row_start).limit(30)
    pages = math.ceil(collection.find({"category_uri":category}).count()/30)
    for c in cursor:
        c["date"] = c["date"].strftime('%Y-%m-%d')
        contents.append(c)
    return render_template('index.html', page=page, pages=pages, contents=contents)

app.run(host="0.0.0.0",port=9999, threaded=True, debug=True)
