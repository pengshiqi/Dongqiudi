# -*- coding:utf-8 -*-

import json
import sqlite3
import time

from pyecharts import Bar, Line, Pie
from pyecharts.engine import create_default_environment


def count():
    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user')
    data = cursor.fetchall()

    # 为渲染创建一个默认配置环境
    # create_default_environment(filet_ype)
    # file_type: 'html', 'svg', 'png', 'jpeg', 'gif' or 'pdf'
    env = create_default_environment("html")

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

    attr1 = ['Male', 'Female', 'unknown']
    v1 = [gender_dict['male'], gender_dict['female'], gender_dict['unknown']]
    gender = Pie("性别")
    gender.add("", attr1, v1, is_label_show=True)

    env.render_chart_to_file(gender, path='./html_files/gender.html')

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

    # 3. 国家队
    # 先获取球队id和名字对应关系字典
    cursor.execute("SELECT * FROM team where league = '国家队'")
    value = cursor.fetchall()

    nation_team_name_dict = dict()
    for x in value:
        nation_team_name_dict[x[5]] = x[3]

    # 然后分析用户数据
    team_dict = dict()
    for x in data:
        if x[7] in nation_team_name_dict.keys():
            if x[7] in team_dict.keys():
                team_dict[x[7]] += 1
            else:
                team_dict[x[7]] = 1

    team_list = [(k, v) for k, v in team_dict.items()]
    team_list = sorted(team_list, key=lambda x: x[1], reverse=True)

    print('国家队 count: ')
    for i in range(5):
        print(nation_team_name_dict.get(team_list[i][0], team_list[i][0]), team_list[i][1])

    attr3 = [nation_team_name_dict.get(x[0], x[0]) for x in team_list]
    v3 = [x[1] for x in team_list]
    nation = Pie("国家队")
    nation.add("", attr3, v3, is_label_show=True)

    env.render_chart_to_file(nation, path='./html_files/nation.html')

    print('-----------------------------------------------------------------------------------')

    # 4. 俱乐部
    # 先获取球队id和名字对应关系字典
    cursor.execute("SELECT * FROM team where league != '国家队'")
    value = cursor.fetchall()

    club_team_name_dict = dict()
    for x in value:
        club_team_name_dict[x[5]] = x[3]

    # 然后分析用户数据
    team_dict = dict()
    for x in data:
        if x[7] in club_team_name_dict.keys():
            if x[7] in team_dict.keys():
                team_dict[x[7]] += 1
            else:
                team_dict[x[7]] = 1

    team_list = [(k, v) for k, v in team_dict.items()]
    team_list = sorted(team_list, key=lambda x: x[1], reverse=True)

    print('俱乐部 count: ')
    for i in range(20):
        print(club_team_name_dict.get(team_list[i][0], team_list[i][0]), team_list[i][1])

    attr4 = [club_team_name_dict.get(x[0], x[0]) for x in team_list[:20]]
    v4 = [x[1] for x in team_list[:20]]
    club = Bar("俱乐部")
    club.add("", attr4, v4, xaxis_interval=0, xaxis_rotate=45, yaxis_rotate=0)

    env.render_chart_to_file(club, path='./html_files/club.html')
    print('-----------------------------------------------------------------------------------')

    cursor.close()
    conn.commit()
    conn.close()


if __name__ == '__main__':
    count()
