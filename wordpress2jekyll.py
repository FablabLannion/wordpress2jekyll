#!/usr/bin/python3
# -*- coding: utf8 -*-

import html2text
import json
import os.path
import requests
import re
import urllib.request
from pprint import pprint as pp

wp_url = "http://fablab-lannion.org"
wp_api = wp_url + '/wp-json/wp/v2/'
wp_upload = "http://fablab-lannion.org/wp-content/uploads"
jekyll_url = "{{ site.url }}"
folder = 'generated'
dl_folder = 'images'
default_author_slug = 'fablab'
default_author_name = 'Fablab Lannion'
default_author_gravatar = 'http://fablablannion.github.io/media/logo.jpg'
unclassed_category = "Non classé"
posts_to_fetch = 179
max_posts_per_req = 100


def call_api(ressource):
    resp = requests.get(ressource)
    # print("call {}".format(ressource))
    if resp.status_code != 200:
        print("    ! Error {} - GET {}".format(resp.status_code, ressource))
        return None
    return resp.json()


def dl_file(url, name):
    if not os.path.isfile(dl_folder+'/'+name):
        print("    DL {}".format(url))
        try:
            urllib.request.urlretrieve(url, dl_folder+'/'+name)
        except UnicodeEncodeError:
            print("    !")
            print("    ! the followin url is bad !, and i can not download it")
            print("    ! {}".format(url))
            print("    ! please download it manually to '{}' folder"
                  .format(dl_folder))
            print("    !")

authors = {default_author_slug: {'fullname': default_author_name,
                                 'gravatar': ''}}

page_count = 0
while posts_to_fetch-page_count*max_posts_per_req > 0:
    print("\nRequest posts {} to {}\n".format(page_count*max_posts_per_req+1,
                                          (page_count+1)*max_posts_per_req))
    page_count += 1
    posts = call_api(wp_api + 'posts?per_page={}&page={}'
                              .format(max_posts_per_req, page_count))
    post_count = 0
    for post in posts:
        post_count += 1
        print("{} - {}\n    Read source '{}'".format(post_count +
                                                     (page_count-1)*
                                                     max_posts_per_req,
                                                     post['slug'],
                                                     post['link']))

        # Get the content
        content = post['content']['rendered']

        # Search for images file to save
        p = re.compile(r'src="({}/.*?)([^/]*?)"'.format(wp_upload))
        wp_imgs = p.findall(content)

        # Download them
        for img in wp_imgs:
            dl_file(img[0]+img[1], img[1])
            # Replace with new url
            p = re.compile(r'{}{}'.format(img[0], img[1]))
            content = p.sub(jekyll_url+'/'+dl_folder+'/'+img[1], content)

        # Search for pdf file to save
        p = re.compile(r'href="({}/.*?)([^/]*?\.pdf)"'.format(wp_upload))
        wp_pdf = p.findall(content)

        # Download them
        for pdf in wp_pdf:
            dl_file(pdf[0]+pdf[1], pdf[1])
            # Replace with new url
            p = re.compile(r'{}{}'.format(pdf[0], pdf[1]))
            content = p.sub(jekyll_url+'/'+dl_folder+'/'+pdf[1], content)

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

        else:
            meta['author'] = default_author_slug
        meta['date'] = post['date'].split('T')[0]
        if 'wp:featuredmedia' in post['_links'].keys():
            feature = call_api(post['_links']['wp:featuredmedia'][0]['href'])
            if feature:
                filename = feature['source_url'].split('/')[-1]
                dl_file(feature['source_url'], filename)
                meta['feature'] = jekyll_url+'/'+dl_folder+'/'+filename
            else:
                print("    !\n    ! Error getting {}\n    !"
                      .format(post['_links']['wp:featuredmedia'][0]['href']))
        meta['tags'] = ["'{}'".format(tag['name']) for tag in call_api(
                       wp_api + 'tags?post={}'.format(post['id']))]
        category = call_api(wp_api +
                            'categories?post={}'.format(post['id']))[
                            0]['name']
        if category != unclassed_category:
            meta['tags'] = category

        # Render the message to a new markdown file
        filename = '{}/{}-{}.md'.format(folder, meta['date'], meta['slug'])
        print("    Generate {}".format(filename))
        with open(filename, 'w') as f:
            print('---', file=f)
            for k, v in meta.items():
                print('{}: {}'.format(k, v), file=f)
            print('---', file=f)
            print(md_content, file=f)
        f.closed

# Print authors list to integrate in _config.yaml
print("\n\nauthors:")
for author, v in authors.items():
    print('    {}:'.format(author))
    print('        name: {}'.format(v['fullname']))
    if v['gravatar']:
        print('        gravatar: {}'.format(v['gravatar']
                                            .split('/')[4]
                                            .split('?')[0]))
