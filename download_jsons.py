#!/usr/bin/env python3

import json
import os
import re
import requests


def get_authtoken():
    with open('./config.json', 'r') as f:
        config = json.load(f)
        authtoken = config['token']
        return authtoken


def download_repos(session, repo_list_fpath, out_fpath):
    print('===== Download Repos Start =====')

    with open(repo_list_fpath, 'r') as f:
        urls = json.load(f)

    result = []
    for url in map(lambda u: u.replace('github.com', 'api.github.com/repos'), urls):
        url = url[:-1] if url[-1] is '/' else url
        print(url)
        response = session.get(url)
        # response.raise_for_status()
        if response.status_code // 100 != 2:
            continue
        j = response.json()
        result.append(j)

    try:
        os.remove(out_fpath)
    except OSError:
        pass
    with open(out_fpath, 'a+') as f:
        f.write(json.dumps(result))

    print('===== Repos Download Complete =====\n\n')


def download_issues(session, repo_json_fpath, out_issues_fpath, out_labels_fpath):
    print('===== Download Issues Start =====')

    with open(repo_json_fpath, 'r') as f:
        repos = json.load(f)

    result = []
    labels = []
    for repo in repos:
        url = repo['url'] + '/issues?state=open'
        page = url
        while page is not None:
            print(page)

            response = session.get(page)
            response.raise_for_status()

            js = response.json()
            for j in js:
                j['repo_id'] = repo['id']

            result += js
            labels += [l['name'] for j in js for l in j['labels']]

            if 'Link' not in response.headers:
                page = None
            else:
                matches = re.findall(r'\<(\S*)\>; rel="next"', response.headers['Link'])
                page = matches[0] if len(matches) > 0 else None

    try:
        os.remove(out_issues_fpath)
        os.remove(out_labels_fpath)
    except OSError:
        pass
    with open(out_issues_fpath, 'a+') as f:
        f.write(json.dumps(result))
    with open(out_labels_fpath, 'a+') as f:
        f.write(json.dumps(list(set(labels))))

    print('===== Download Issues Complete =====\n\n')


def download():
    authtoken = get_authtoken()
    if authtoken is None:
        raise Exception('Autoken not set in config.json')

    s = requests.Session()
    s.headers.update({'Accept': 'application/vnd.github.v3+json'})
    s.headers.update({'Authorization': 'token %s' % authtoken})

    os.makedirs('./data/', mode=0o755, exist_ok=True)
    download_repos(s, './data/url_list.json', './data/repos.json')
    download_issues(s, './data/repos.json', './data/issues.json', './data/labels.json')


if __name__ == '__main__':
    download()
