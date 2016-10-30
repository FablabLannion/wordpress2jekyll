#!/usr/bin/python3
# -*- coding: utf8 -*-

import html2text
import json
import requests
import yaml

wp_url = "http://fablab-lannion.org"
wp_api = wp_url + '/wp-json/wp/v2/'
folder = 'generated'
default_author_name = 'Fablab Lannion'
default_author_gravatar = 'http://fablablannion.github.io/media/logo.jpg'


def call_api(ressource):
    resp = requests.get(ressource)
    if resp.status_code != 200:
        print("Error {} - GET {}".format(resp.status_code, ressource))
        return None
    return resp.json()

print("Request pages")
posts = call_api(wp_api + 'posts?per_page=10')

for post in posts:
    print("Read {}".format(post['slug']))
    content = html2text.html2text(post['content']['rendered'])
    meta = dict()
    meta['slug'] = post['slug']
    meta['layout'] = 'post'
    meta['comments'] = True
    # meta['permalink'] = post['link']
    meta['title'] = post['title']['rendered']
    author_h = call_api(post['_links']['author'][0]['href'])
    if author_h:
        author = author_h['name']
        meta['author_gravatar'] = author_h["avatar_urls"]['96']
    else:
        author = default_author_name
        meta['author_gravatar'] = default_author_gravatar
    meta['date'] = post['date'].split('T')[0]
    if 'wp:featuredmedia' in post['_links'].keys():
        meta['feature'] = call_api(post['_links']['wp:featuredmedia']
                                       [0]['href'])['source_url']
    meta['tags'] = [tag['name'] for tag in call_api(
                   wp_api + 'tags?post={}'.format(post['id']))]

    # Render the message to a new markdown file
    filename = '{}/{}-{}.md'.format(folder, meta['date'],meta['slug'])
    print("Generate {}".format(filename))
    with open(filename, 'w') as f:
        print('---', file=f)
        for k,v in meta.items():
            print('{}: {}'.format(k, v), file=f)
        print('---', file=f)
        print(content, file=f)
    f.closed
