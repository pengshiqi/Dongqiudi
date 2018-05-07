# -*- coding: utf-8 -*-

import requests
import json
import sqlite3
import time

from util import get_user_info, get_comment_user, get_articles_id


def write_team_info():
    """
    获取各个球队的信息，并存储在本地的sqlite数据库中。(data.db -> team)

    :return:
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'Cookie': 'dqduid=ChM8uVrpeZitQxLPAysBAg==; Hm_lvt_662abe3e1ab2558f09503989c9076934=1525250495; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22163200395eeaa4-0459f11ab28432-336b7b05-1024000-163200395f0288%22%2C%22%24device_id%22%3A%22163200395eeaa4-0459f11ab28432-336b7b05-1024000-163200395f0288%22%2C%22props%22%3A%7B%22%24latest_referrer%22%3A%22%E5%8F%96%E5%80%BC%E5%BC%82%E5%B8%B8%22%2C%22%24latest_referrer_host%22%3A%22%E5%8F%96%E5%80%BC%E5%BC%82%E5%B8%B8%22%7D%7D; Hm_lpvt_662abe3e1ab2558f09503989c9076934=1525403827; laravel_session=eyJpdiI6InJJVW50dzErb1FQNWVLOGd6XC9YbEtvTk5mVkZoTUI0blpIYVEzaUN1bVQ0PSIsInZhbHVlIjoiSXVacTExaXl1aldzV1c4cXVmRTIyczl0S0RONzhHNVRGT2Z6WWFwU0d0QkZ2NlJLY3ljeG92MVFsN0xLXC92anBSMmh2bHJOMVl1MnhKZzVWbWtzYmFBPT0iLCJtYWMiOiIxZWI1NTJiY2ZhNDFkNDk5MTgyYzgxOTQwNWVkYWM4YjJjMTEzZGNkZTUwODc1MTJhMDViMTMyN2NhNmVkOTZmIn0%3D'
    }

    BASE_URL = 'http://api.dongqiudi.com'

    # 1. 获取左侧tab
    URL = '/catalogs'
    r = requests.get(url=BASE_URL + URL, headers=headers)
    tab_content = json.loads(r.text)
    # print(tab_content)

    # 用来存储数据，然后一起写入数据库
    team_data = list()

    for item in tab_content:
        # 跳过热门
        if item['id'] in (1, 9, 10, 11):
            continue

        URL = '/catalog/channels/'
        r = requests.get(url=BASE_URL + URL + str(item['id']), headers=headers)
        content = json.loads(r.text)

        team_data.append(content)

    # 存入 sqlite3 数据库
    # 连接到SQLite数据库
    # 数据库文件是 data.db
    # 如果文件不存在，会自动在当前目录创建:
    conn = sqlite3.connect('data.db')

    # 创建一个Cursor:
    cursor = conn.cursor()
    # 判断表是否存在，如果存在则删除
    cursor.execute("select * from sqlite_master where type = 'table' and name = 'team'")
    # 获取查询结果
    value = cursor.fetchall()
    if value:
        cursor.execute('DROP TABLE team')

    # 执行一条SQL语句，创建team表:
    cursor.execute('CREATE TABLE team (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, league VARCHAR(20), '
                   'avatar VARCHAR(100), name VARCHAR(40), team_id VARCHAR(10), object_id VARCHAR(10))')

    # 插入记录:
    # cursor.execute('INSERT INTO user (id, name) VALUES (\'1\', \'Michael\')')
    for league_data in team_data:
        league_name = league_data['title']
        for team in league_data['data']:
            cursor.execute("INSERT INTO team (league, avatar, name, team_id, object_id) VALUES "
                           "('{}', '{}', '{}', '{}', '{}')".format(league_name, team.get('avatar', ''),
                                                                   team.get('name', ''), team.get('id', ''),
                                                                   team.get('object_id', '')))

        print('{} data finish.'.format(league_name))

    # 关闭Cursor:
    cursor.close()
    # 提交事务:
    conn.commit()
    # 关闭Connection:
    conn.close()


def write_article_comment_user(page_num):
    """
    将前 page num 页文章的评论区的用户id写入 article_comment_user 列表。

    :param page_num: 前 page num 页文章
    :return:
    """
    tic = time.time()
    # --------------------- 1. 获取文章id列表 ---------------------
    article_id_dict = get_articles_id(page_num)
    article_id_list = list(article_id_dict.values())
    # flatten
    article_id_list = [y for x in article_id_list for y in x]

    print(f'Article id list obtained, there are total {len(article_id_list)} articles.')

    toc1 = time.time()

    print(f'Part 1 costs time: {toc1 - tic} second.')

    # --------------------- 2. 获取各文章下的用户id列表 ---------------------
    user_id_list = list()

    count = 0
    total_users = 0
    for article_id in article_id_list:
        user_set = get_comment_user(article_id)
        user_id_list.append([article_id, str(user_set)])

        count += 1
        total_users += len(user_set)
        if count % 10 == 0:
            print(f'{count} articles have been processed, there are total {total_users} users.')

    print(f'User id set obtained, there are total {total_users} users.')

    toc2 = time.time()

    print(f'Part 2 costs time: {toc2 - toc1} second.')

    # --------------------- 3. 写入数据库 ---------------------
    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()
    cursor.execute("select * from sqlite_master where type = 'table' and name = 'article_comment_user'")
    value = cursor.fetchall()
    if value:
        cursor.execute('DROP TABLE article_comment_user')

    cursor.execute('CREATE TABLE article_comment_user (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
                   'article_id VARCHAR(20), user_id_set VARCHAR(10000))')

    cursor.executemany(f"INSERT INTO article_comment_user (article_id, user_id_set) VALUES (?, ?)", user_id_list)

    cursor.close()
    conn.commit()
    conn.close()

    toc3 = time.time()

    print(f'Part 3 costs time: {toc3 - toc2} second.')


def write_user_info():
    tic = time.time()

    # 1. 先读取user id列表，并去重
    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()
    cursor.execute('select * from article_comment_user')
    value = cursor.fetchall()

    user_id_set = set()
    for x in value:
        d = eval(x[2])
        user_id_set.update(d)

    print(f'There are {len(user_id_set)} users in total.')

    toc1 = time.time()
    print(f'Part 1 finish, cost time {toc1 - tic} second.')

    # 2. 获取用户信息，写入user表
    cursor.execute("select * from sqlite_master where type = 'table' and name = 'user'")
    value = cursor.fetchall()
    if value:
        cursor.execute('DROP TABLE user')

    cursor.execute('CREATE TABLE user (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id VARCHAR(20), '
                   'user_name VARCHAR(50), gender VARCHAR(10), created_at VARCHAR(30), region_id INTEGER, '
                   'region_phrase VARCHAR(15), team_id VARCHAR(10), introduction VARCHAR(20), timeline_total INTEGER, '
                   'post_total INTEGER, reply_total INTEGER, up_total VARCHAR(10), following_total VARCHAR(10), '
                   'followers_total VARCHAR(10))')

    insert_data = list()
    count = 0
    for user_id in user_id_set:
        user_info = get_user_info(user_id)
        insert_data.append(user_info)

        count += 1
        if count % 200 == 0:
            print(f'{count} users have been processed.')

    cursor.executemany(f"INSERT INTO user (user_id, user_name, gender, created_at, region_id, region_phrase, "
                       f"team_id, introduction, timeline_total, post_total, reply_total, up_total, following_total, "
                       f"followers_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", insert_data)

    cursor.close()
    conn.commit()
    conn.close()

    toc2 = time.time()

    print(f'Part 2 costs time: {toc2 - toc1} second.')


if __name__ == '__main__':

    # 获取球队信息，写入 team 表
    # write_team_info()

    # write_article_comment_user(100)

    write_user_info()

