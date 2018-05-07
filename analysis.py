# -*- coding:utf-8 -*-

import json
import sqlite3
import time


def count():
    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user')
    data = cursor.fetchall()

    # 1. gender
    gender_dict = {'male': 0, 'female': 0, 'unknown': 0}
    for x in data:
        if x[3] == 'male':
            gender_dict['male'] += 1
        elif x[3] == 'female':
            gender_dict['female'] += 1
        else:
            gender_dict['unknown'] += 1

    print("There are {} male users, {} female users, and {} users gender unknown.".format(gender_dict['male'],
                                                                                          gender_dict['female'],
                                                                                          gender_dict['unknown']))

    print('-----------------------------------------------------------------------------------')

    # 2. 地区
    region_dict = dict()
    for x in data:
        if x[6] in region_dict.keys():
            region_dict[x[6]] += 1
        else:
            region_dict[x[6]] = 1

    region_list = [(k, v) for k, v in region_dict.items()]
    region_list = sorted(region_list, key=lambda x: x[1], reverse=True)

    print('Region count: ')
    for i in range(30):
        if region_list[i][0]:
            print(region_list[i][0], end=',')
            print(region_list[i][1])
        else:
            print('None', end=',')
            print(region_list[i][1])
    print('-----------------------------------------------------------------------------------')

    # 3. team
    # 先获取球队id和名字对应关系字典
    cursor.execute('SELECT * FROM team')
    value = cursor.fetchall()

    team_name_dict = dict()
    for x in value:
        team_name_dict[x[5]] = x[3]

    # 然后分析用户数据
    team_dict = dict()
    for x in data:
        if x[7] in team_dict.keys():
            team_dict[x[7]] += 1
        else:
            team_dict[x[7]] = 1

    team_list = [(k, v) for k, v in team_dict.items()]
    team_list = sorted(team_list, key=lambda x: x[1], reverse=True)

    print('Team count: ')
    for i in range(30):
        print(team_name_dict.get(team_list[i][0], team_list[i][0]), team_list[i][1])
    print('-----------------------------------------------------------------------------------')

    cursor.close()
    conn.commit()
    conn.close()


if __name__ == '__main__':
    count()
