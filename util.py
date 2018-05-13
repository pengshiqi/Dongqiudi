# -*- coding: utf-8 -*-

import requests
import json
import sqlite3
import time
import asyncio

from pprint import pprint


def get_articles_id(page_num):
    """
    获取前 page_num 页的 article id.

    :param page_num:
    :return: id dict, key 为日期, value 为当日的所有 article id 列表。
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    URL = 'http://api.dongqiudi.com/app/tabs/iphone/1.json'
    r = requests.get(url=URL, headers=headers)
    data = json.loads(r.text)
    next_url = data['next']

    id_dict = dict()

    for i in range(page_num):
        r = requests.get(url=next_url, headers=headers)
        data = json.loads(r.text)

        for article in data['articles']:
            publish_date = article['published_at']
            if publish_date[:10] in id_dict.keys():
                id_dict[publish_date[:10]].append(article['id'])
            else:
                id_dict[publish_date[:10]] = [article['id']]

        next_url = data['next']

        if i % 25 == 0:
            print(f'{i} pages of articles have been obtained.')

    # pprint(id_dict)

    return id_dict


def get_comment_user(article_id):
    """
    获取某 article 下评论区的用户id (去重)。

    :param article_id:
    :return: 用户id set
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    BASE_URL = 'http://api.dongqiudi.com/v2/article/{}/comment?sort=down&version=600'

    try:
        r = requests.get(url=BASE_URL.format(article_id), headers=headers, timeout=10)
        data = json.loads(r.text)
    except:
        data = {'data': {}}

    if 'data' not in data.keys():
        return set([])

    user_list = list()
    for user in data['data'].get('user_list', []):
        user_list.append(user.get('id', ''))

    next_url = data['data'].get('next', '')

    while next_url:
        try:
            r = requests.get(url=next_url, headers=headers, timeout=10)
            data = json.loads(r.text)
        except:
            data = {'data': {}}

        if 'data' not in data.keys():
            break

        for user in data['data'].get('user_list', []):
            user_list.append(user.get('id', ''))

        next_url = data['data'].get('next', '')

    user_set = set(user_list)

    user_set.discard('0')
    user_set.discard('99999999')

    # print(user_set)

    return user_set


def get_user_info(user_id):
    """
    获取某个用户的信息。

    :param user_id: 用户id
    :return: 用户id，用户名，性别，创建时间，地区id，地区名，球队id，介绍，timeline total，发表数，回复数，被点赞数，关注数，被关注数
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    url = 'https://api.dongqiudi.com/users/profile/{}'.format(user_id)

    r = requests.get(url=url, headers=headers)
    data = json.loads(r.text)

    try:
        return data['user'].get('user_id', user_id), data['user']['username'], \
               data['user'].get('gender', None), data['user']['created_at'], \
               data['user']['region']['id'] if data['user']['region'] else None, \
               data['user']['region']['phrase'] if data['user']['region'] else None, \
               data['user'].get('team_id', None), data['user']['introduction'], \
               data['user']['timeline_total'], data['user']['post_total'], data['user']['reply_total'], \
               data['user']['up_total'], data['user']['following_total'], data['user']['followers_total']
    except:
        print(f'{user_id} has an exception.')
        return user_id, None, None, None, None, None, None, None, None, None, None, None, None, None, None


if __name__ == '__main__':
    tic = time.time()

    # 获取球队信息，写入 team 表
    # get_team_info()

    # 函数测试
    # get_articles_id(30)
    get_comment_user('642005')
    # print(get_user_info('0'))
