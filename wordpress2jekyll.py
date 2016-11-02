#!/usr/bin/python3
# -*- coding: utf8 -*-

import html2text
import json
import requests
import re
import urllib.request
from pprint import pprint as pp

wp_url = "http://fablab-lannion.org"
wp_api = wp_url + '/wp-json/wp/v2/'
wp_upload = "http://fablab-lannion.org/wp-content/uploads"
wp_newurl = "http://fablablannion.github.io"
folder = 'generated'
dl_folder = 'images'
default_author_slug = 'fablab'
default_author_fullname = 'Fablab Lannion'
default_author_gravatar = 'http://fablablannion.github.io/media/logo.jpg'
unclassed_category = "Non classé"


def call_api(ressource):
    resp = requests.get(ressource)
    # print("call {}".format(ressource))
    if resp.status_code != 200:
        print("Error {} - GET {}".format(resp.status_code, ressource))
        return None
    return resp.json()

print("Request pages")
posts = call_api(wp_api + 'posts?per_page=20')

authors = {default_author_slug: {'fullname': default_author_fullname,
                                 'gravatar': ''}}

for post in posts:
    print("Read {}".format(post['slug']))

    # Get the content
    content = post['content']['rendered']

    # Search for WP file to save
    p = re.compile(r'src="({}/.*?)([^/]*?)"'.format(wp_upload))
    wp_imgs = p.findall(content)

    # Download them
    for img in wp_imgs:
        print("DL {}{}".format(img[0], img[1]))
        try:
            urllib.request.urlretrieve(img[0]+img[1], dl_folder+'/'+img[1])
        except UnicodeEncodeError:
            print("! the followin url is bad !, and i can not download it")
            print("! {}{}".format(img[0], img[1]))
            print("please download it manually to {}".format(dl_folder))
        # Replace with new url
        p = re.compile(r'{}{}'.format(img[0], img[1]))
        content = p.sub(wp_newurl+'/'+dl_folder+'/'+img[1], content)

    # Translate HTML to MD
    md_content = html2text.html2text(content)

    # Recover metadata
    meta = dict()
    meta['slug'] = post['slug']
    meta['layout'] = 'post'
    meta['comments'] = True
    meta['title'] = '"{}"'.format(post['title']['rendered'])
    author_h = call_api(post['_links']['author'][0]['href'])
    if author_h:
        meta['author'] = author_h['slug']
        authors[author_h['slug']] = {'fullname': author_h['name'],
                                     'gravatar': author_h["avatar_urls"]['96']}
        meta['author_fullname'] = author_h['name']
        meta['author_gravatar'] = author_h["avatar_urls"]['96']

    else:
        meta['author'] = default_author_slug
        meta['author_fullname'] = default_author_name
        meta['author_gravatar'] = default_author_gravatar
    meta['date'] = post['date'].split('T')[0]
    if 'wp:featuredmedia' in post['_links'].keys():
        meta['feature'] = call_api(post['_links']['wp:featuredmedia']
                                       [0]['href'])['source_url']
    meta['tags'] = [tag['name'] for tag in call_api(
                   wp_api + 'tags?post={}'.format(post['id']))]
    category = call_api(wp_api +
                        'categories?post={}'.format(post['id']))[
                        0]['name']
    if category != unclassed_category:
        meta['tags'] = category

    # Render the message to a new markdown file
    filename = '{}/{}-{}.md'.format(folder, meta['date'], meta['slug'])
    print("Generate {}".format(filename))
    with open(filename, 'w') as f:
        print('---', file=f)
        for k, v in meta.items():
            print('{}: {}'.format(k, v), file=f)
        print('---', file=f)
        print(md_content, file=f)
    f.closed

# Print authors list to integrate in _config.yaml
print('authors:')
for author, v in authors.items():
    print('    {}:'.format(author))
    print('        name: {}'.format(v['fullname']))
    if v['gravatar']:
        print('        gravatar: {}'.format(v['gravatar']
                                            .split('/')[4]
                                            .split('?')[0]))
