# -*- coding: utf-8 -*-

import requests
import json
import sqlite3
import time
import multiprocessing
import argparse

from util import get_user_info, get_comment_user, get_articles_id


def write_team_info():
    """
    获取各个球队的信息，并存储在本地的sqlite数据库中。(data.db -> team)

    :return:
    """

    # 使用时需要将 Cookie 替换。
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'Cookie': 'laravel_session=eyJpdiI6ImtucXJlaTdDdnlCWHJOaDl6Q3pnNlZkcUgxU0FpVE5IZDBuWGt1a3pha2c9IiwidmFsdWUiOiJNQ0ZzNXZla2hsaWtENEEraERQQW1adXFRdUdCUlBGV25MQ09SMW5jek1EV2xPaG5sV05VSGFHMUkxSDVEM1pBVWJsWFBZMUQ1SnRCQnREZlBrRUJ5dz09IiwibWFjIjoiOGE3NzY2YWE3NTlmYjIyODg5M2U4ZjBlMDc4NzU5NzgzYmM2NDIwOTY2MTU0NmI4Zjc5OTFjMWM5YmQ1YzZmMSJ9; expires=Sat, 12-May-2018 13:55:57 GMT; Max-Age=7200; path=/; domain=dongqiudi.com; httponly'
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

        print('{} data finish.'.format(league_name.encode(encoding='utf-8')))

    # 关闭Cursor:
    cursor.close()
    # 提交事务:
    conn.commit()
    # 关闭Connection:
    conn.close()


def write_article_comment_user(page_num, obtain_article=True, multi_process=False, if_continue=False):
    """
    将前 page num 页文章的评论区的用户id写入 article_comment_user 列表。

    :param page_num: 前 page num 页文章
    :param obtain_article: 是否要运行part 1来获取文章列表
    :param multi_process: 是否启动多线程
    :param if_continue: 是否继续上次的请求
    :return:
    """
    tic = time.time()
    # --------------------- 1. 获取文章id列表 ---------------------
    if obtain_article:
        article_id_dict = get_articles_id(page_num)
        article_id_list = list(article_id_dict.values())
        # flatten
        article_id_list = [y for x in article_id_list for y in x]

        print(f'Article id list obtained, there are total {len(article_id_list)} articles.')

        with open('article_id.txt', 'wb') as F:
            F.write(str(article_id_list).encode(encoding='utf-8'))

    toc1 = time.time()

    print(f'Part 1 costs time: {toc1 - tic} second.')

    # --------------------- 2. 获取各文章下的用户id列表 ---------------------
    # 数据库
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # 如果不是继续上次的，就清空表
    if not if_continue:
        cursor.execute("select * from sqlite_master where type = 'table' and name = 'article_comment_user'")
        value = cursor.fetchall()
        if value:
            cursor.execute('DROP TABLE article_comment_user')

        cursor.execute('CREATE TABLE article_comment_user (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
                       'article_id VARCHAR(20), user_id_set VARCHAR(10000))')

    user_id_list = list()
    count = 0
    total_users = 0

    with open('article_id.txt', 'rb') as F:
        d = F.readlines()
        article_id_list = eval(d[0])

    with open('crawled_article_id.txt', 'rb') as F:
        d = F.readlines()
        crawled_article_id_list = eval(d[0])

    article_id_list = list(set(article_id_list) - set(crawled_article_id_list))

    # 单进程
    if not multi_process:
        for article_id in article_id_list:
            user_set = get_comment_user(article_id)
            user_id_list.append([article_id, str(user_set)])
            crawled_article_id_list.append(article_id)

            count += 1
            total_users += len(user_set)
            if count % 20 == 0:
                print(f'{count} articles have been processed, there are total {total_users} users.')

            if count % 1000 == 0:
                # 将当前数据写入数据库
                cursor.executemany(f"INSERT INTO article_comment_user (article_id, user_id_set) VALUES (?, ?)",
                                   user_id_list)

                cursor.close()
                conn.commit()

                user_id_list = list()
                cursor = conn.cursor()

                with open('crawled_article_id.txt', 'wb') as F:
                    F.write(str(crawled_article_id_list).encode(encoding='utf-8'))

    else:
        # 多进程
        pool = multiprocessing.Pool(8)
        for article_id in article_id_list:
            result = pool.apply_async(get_comment_user, (article_id,))
            user_set = result.get()
            user_id_list.append([article_id, str(user_set)])

            count += 1
            total_users += len(user_set)
            if count % 10 == 0:
                print(f'{count} articles have been processed, there are total {total_users} users.')

        pool.close()
        pool.join()

    print(f'User id set obtained, there are total {total_users} users.')

    toc2 = time.time()

    print(f'Part 2 costs time: {toc2 - toc1} second.')

    # --------------------- 3. 写入数据库 ---------------------

    cursor.executemany(f"INSERT INTO article_comment_user (article_id, user_id_set) VALUES (?, ?)", user_id_list)

    cursor.close()
    conn.commit()

    conn.close()

    toc3 = time.time()

    print(f'Part 3 costs time: {toc3 - toc2} second.')


def write_user_list():
    """
    将带爬取的用户id列表写入 user_id_set.txt 。

    :return:
    """
    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()
    cursor.execute('select * from article_comment_user')
    value = cursor.fetchall()

    user_id_set = set()
    for x in value:
        d = eval(x[2])
        user_id_set.update(d)

    print(f'There are {len(user_id_set)} users in total.')

    cursor.close()
    conn.commit()
    conn.close()

    with open('user_id_set.txt', 'wb') as F:
        F.write(str(list(user_id_set)).encode(encoding='utf-8'))


def write_user_info(begin, end):
    tic = time.time()

    # 1. 先读取user id列表
    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()

    with open('user_id_set.txt', 'rb') as F:
        d = F.readlines()
        res = eval(d[0])
        user_id_set = set(res[begin: end])

    toc1 = time.time()
    print(f'Part 1 finish, cost time {toc1 - tic} second.')

    # 2. 获取用户信息，写入user表

    insert_data = list()
    count = 0
    for user_id in user_id_set:
        try:
            user_info = get_user_info(user_id)
        except:
            continue
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
    parser = argparse.ArgumentParser(description='Parse arguments.')
    parser.add_argument('--begin',  type=int, default=0,
                        help='begin index')
    parser.add_argument('--end',  type=int, default=610803,
                        help='end index')

    args = parser.parse_args()

    # 获取球队信息，写入 team 表
    write_team_info()

    # write_article_comment_user(5000, obtain_article=False, multi_process=False, if_continue=True)

    # write_user_list()

    # write_user_info(args.begin, args.end)


