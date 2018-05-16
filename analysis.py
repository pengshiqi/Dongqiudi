# -*- coding:utf-8 -*-

import sqlite3
import datetime

import jieba

from pyecharts import Bar, Line, Pie, Map, Page, Style, WordCloud
from pyecharts.engine import create_default_environment


def process_league_data(league_name, cursor, data, env, figure_type='pie', limit=None):
    """
    画某个联赛的饼图。

    :param league_name: 联赛名
    :param cursor:
    :param data:
    :param env:
    :param figure_type: pie 饼图， bar 柱状图
    :param limit: 画柱状图时的俱乐部数量
    :return: None
    """
    # 先获取球队id和名字对应关系字典
    if league_name == '俱乐部':
        cursor.execute("SELECT * FROM team where league != '国家队'")
    else:
        cursor.execute(f"SELECT * FROM team where league = '{league_name}'")
    value = cursor.fetchall()

    team_name_dict = dict()
    for x in value:
        team_name_dict[x[5]] = x[3]

    # 然后分析用户数据
    team_dict = dict()
    for x in data:
        if x[7] in team_name_dict.keys():
            if x[7] in team_dict.keys():
                team_dict[x[7]] += 1
            else:
                team_dict[x[7]] = 1

    # 排序
    team_list = [(k, v) for k, v in team_dict.items()]
    team_list = sorted(team_list, key=lambda x: x[1], reverse=True)

    print(f'{league_name} count: ')
    for i in range(len(team_list)):
        print(team_name_dict.get(team_list[i][0], team_list[i][0]), team_list[i][1])

    attr = [team_name_dict.get(x[0], x[0]) for x in team_list]
    v = [x[1] for x in team_list]

    if limit:
        attr = attr[:limit]
        v = v[:limit]

    if figure_type == 'bar':
        league = Bar(f"{league_name}")
        league.add("", attr, v, is_label_show=True, is_legend_show=False, xaxis_rotate=45)
    else:
        league = Pie(f"{league_name}")
        league.add("", attr, v, is_label_show=True, is_legend_show=False)

    env.render_chart_to_file(league, path=f'./html_files/{league_name}.html')
    print('-----------------------------------------------------------------------------------')


def analyse(calculate_word_cloud=True):
    """
    分析 data.db -> user 的用户数据。

    :param calculate_word_cloud: 是否计算词云，这个比较花费时间。
    :return:
    """
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

    print('Top30 region count: ')
    for i in range(30):
        if region_list[i][0]:
            print(region_list[i][0], end=',')
            print(region_list[i][1])
        else:
            print('None', end=',')
            print(region_list[i][1])

    style = Style(
        width=1100, height=600
    )

    # 1是中国数据，2是世界数据
    china_data_dict = dict()
    v1 = list()
    v2 = list()
    a1 = list()
    a2 = list()

    # 国家名字典
    country_name_dict = {'西班牙': 'Spain', '英国': 'United Kingdom', '美国': 'United States', '俄罗斯': 'Russia',
                         '意大利': 'Italy', '加拿大': 'Canada', '澳大利亚': 'Australia', '日本': 'Japan',
                         '法国': 'France', '韩国': 'Korea', '巴西': 'Brazil', '新加坡': 'Singapore',
                         '马来西亚': 'Malaysia', '泰国': 'Thailand', '中国': 'China', '其他': 'Unknown Country'}

    for item in region_list:
        if item[0]:
            x = item[0].split()
            if x[0] != '海外':
                if x[0] in china_data_dict.keys():
                    china_data_dict[x[0]] += item[1]
                else:
                    china_data_dict[x[0]] = item[1]
            else:
                if x[1] != '其他':
                    a2.append(country_name_dict.get(x[1], x[1]))
                    v2.append(item[1])

    for k, v in china_data_dict.items():
        a1.append(k)
        v1.append(v)

    # 加上中国的数据
    # a2.append('China')
    # v2.append(sum(v1))

    # 归一化到 0 - 100
    def normalize(l):
        m = min(l)
        l = [x - m for x in l]
        m = max(l)
        l = [x / m * 100 for x in l]
        return l

    v1 = normalize(v1)
    v2 = normalize(v2)

    # 输出html
    chart = Map("国内懂球帝分布", **style.init_style)
    chart.add("", a1, v1, maptype='china', is_visualmap=True,
              visual_text_color='#000')
    env.render_chart_to_file(chart, path='./html_files/china_distribution.html')

    # 输出html
    chart = Map("海外懂球帝分布", **style.init_style)
    chart.add("", a2, v2, maptype='world', is_visualmap=True,
              visual_text_color='#000')
    env.render_chart_to_file(chart, path='./html_files/world_distribution.html')

    print('-----------------------------------------------------------------------------------')

    # 3. 联赛
    process_league_data('国家队', cursor, data, env)

    process_league_data('中超', cursor, data, env)
    process_league_data('英超', cursor, data, env)
    process_league_data('西甲', cursor, data, env)
    process_league_data('意甲', cursor, data, env)
    process_league_data('德甲', cursor, data, env)
    process_league_data('法甲', cursor, data, env)
    process_league_data('国内', cursor, data, env)

    process_league_data('俱乐部', cursor, data, env, figure_type='bar', limit=20)

    print('-----------------------------------------------------------------------------------')

    # 4. name word cloud
    if calculate_word_cloud:
        name_list = [x[2] for x in data]

        jieba.load_userdict('dict.txt')

        cut_name_list = [jieba.cut(x, cut_all=False) for x in name_list]
        # cut_name_list = [jieba.cut_for_search(x) for x in name_list]

        #加载停用词表
        stop = [line.strip() for line in open('stop_words.txt').readlines()]

        word_dict = dict()
        for cut_name in cut_name_list:
            for word in cut_name:
                if word not in stop:
                    if word in word_dict.keys():
                        word_dict[word] += 1
                    else:
                        word_dict[word] = 1

        value_list = [(k, v) for k, v in word_dict.items()]
        value_list = sorted(value_list, key=lambda x: x[1], reverse=True)

        # 去掉单字
        attr = [x[0] for x in value_list if len(x[0]) > 1]
        value = [x[1] for x in value_list if len(x[0]) > 1]

        # 取 top 100
        attr = attr[:100]
        value = value[:100]

        wordcloud = WordCloud(width=1300, height=620)
        wordcloud.add("", attr, value, word_size_range=[20, 100])

        env.render_chart_to_file(wordcloud, path='./html_files/word_cloud.html')
    print('-----------------------------------------------------------------------------------')

    # 5. 加入时间
    join_time = [int(x[8][6:-1]) for x in data if x[8][6:-1]]

    join_time_dict = dict()
    for x in join_time:
        if x in join_time_dict.keys():
            join_time_dict[x] += 1
        else:
            join_time_dict[x] = 1

    join_time_list = [(k, v) for k, v in join_time_dict.items()]
    join_time_list = sorted(join_time_list, key=lambda x: x[0])

    attr = [x[0] for x in join_time_list]
    v = [x[1] for x in join_time_list]

    t = datetime.datetime(2018, 5, 12)
    attr = [t - datetime.timedelta(days=x) for x in attr]
    attr = [f'{x.year}-{x.month}-{x.day}' for x in attr]

    bar = Bar(f"加入时间")
    bar.add("", attr, v, is_stack=True)

    env.render_chart_to_file(bar, path='./html_files/join_time.html')

    print('-----------------------------------------------------------------------------------')

    # 6. post times
    post_time = [int(x[10]) for x in data if x[10] and int(x[10]) >= 0]

    post_time_dict = dict()
    for x in post_time:
        if x in post_time_dict.keys():
            post_time_dict[x] += 1
        else:
            post_time_dict[x] = 1

    post_time_list = [(k, v) for k, v in post_time_dict.items()]
    post_time_list = sorted(post_time_list, key=lambda x: x[0])

    attr = [x[0] for x in post_time_list]
    v = [x[1] for x in post_time_list]

    bar = Bar(f"Post times")
    bar.add("", attr, v, is_stack=True)

    env.render_chart_to_file(bar, path='./html_files/post_times.html')

    print('-----------------------------------------------------------------------------------')

    # 6. reply times
    reply_time = [int(x[11]) for x in data if x[11] and int(x[11]) >= 0]

    reply_time_dict = dict()
    for x in reply_time:
        if x in reply_time_dict.keys():
            reply_time_dict[x] += 1
        else:
            reply_time_dict[x] = 1

    reply_time_list = [(k, v) for k, v in reply_time_dict.items()]
    reply_time_list = sorted(reply_time_list, key=lambda x: x[0])

    attr = [x[0] for x in reply_time_list]
    v = [x[1] for x in reply_time_list]

    bar = Bar(f"Reply times")
    bar.add("", attr, v, is_stack=True)

    env.render_chart_to_file(bar, path='./html_files/reply_times.html')

    print('-----------------------------------------------------------------------------------')

    cursor.close()
    conn.commit()
    conn.close()


if __name__ == '__main__':
    analyse(calculate_word_cloud=False)
