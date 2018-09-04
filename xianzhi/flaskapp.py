# -*- coding: utf-8 -*-
import re
import os
import math
import pymongo
from flask import Flask, request, render_template, send_file, abort
# setting:
MONGODB_SERVER = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'xianzhi'
MONGODB_COLLECTION = 'xianzhi_list'
ROWS_PER_PAGE = 20

app = Flask(__name__, static_url_path="", static_folder='xzsite')
app.config.from_object(__name__)
# monogodb connection string
connection_string = "mongodb://%s:%d" % (
    app.config['MONGODB_SERVER'], app.config['MONGODB_PORT'])


def get_contents(bytext="", byauthor="", bycategory="", row_start=0):
    # return pages , contents
    client = pymongo.MongoClient(connection_string)
    db = client["xianzhi"]
    collection = db["xianzhi_list"]
    find_dic = {}
    arg = ""
    if bytext:
        kws = [ks for ks in bytext.strip().split(' ') if ks != '']
        if len(kws) > 0:
            reg_pattern = re.compile('|'.join(kws), re.IGNORECASE)
            find_dic['text'] = reg_pattern
            arg += '&keyword={}'.format(bytext)
    if byauthor:
        find_dic['author'] = byauthor
        arg += '&author={}'.format(byauthor)
    if bycategory:
        find_dic['category'] = bycategory
        arg += '&category={}'.format(bycategory)
    find_result = collection.find(find_dic)
    cursor = find_result.sort('date', pymongo.DESCENDING).skip(row_start).limit(30)
    pages = math.ceil(find_result.count()/30)
    contents = []
    for c in cursor:
        c["date"] = c["date"].strftime('%Y-%m-%d')
        contents.append(c)
    return pages, contents, arg


@app.route('/search')
@app.route('/')
def index():
    contents = []
    page = request.args.get("page", '1')
    if not page.isdigit():
        page = 1
    page = int(page)
    bytext = request.args.get('keyword', "")
    byauthor = request.args.get('author', "")
    bycategory = request.args.get('category', "")
    row_start = (int(page) - 1)*30
    pages, contents, arg = get_contents(
        bytext, byauthor, bycategory, row_start)
    return render_template('index.html', page=page, pages=pages, contents=contents, arg=arg)


@app.route("/<tid>")
def tidhtml(tid):
    if os.path.exists("xzsite/{}".format(tid)):
        return send_file("xzsite/{}".format(tid))
    else:
        return abort(404)


app.run(host="0.0.0.0", threaded=True, debug=True)
