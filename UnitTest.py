#!/usr/bin/python
# -*- coding: utf-8 -*-

import config
import json
from BayesEngine import BayesEngine, getUserBehavior, getMoviesInfo
from ALSEngine import ALSEngine, read_data
from LSIEngine import LSIEngine, readItemInfos
import sys
import random
from scipy.sparse import coo_matrix
from pandas import DataFrame 
from math import sqrt

def test1(b, info):
    if True:
        print "喜欢：银河系漫游指南(1292267)"
        print "不喜欢：东京爱情故事(1438760)"
        n2 = b.recommend(dict([(1292267L, 0), (1438760L, 1)]))
        print "推荐：", info[n2]['title'], "(", n2, ")"

    if True:
        print "喜欢：东京爱情故事(1438760)"
        print "不喜欢：银河系漫游指南(1292267)"
        n2 = b.recommend(dict([(1438760L, 0), (1292267L, 1)]))
        print "推荐：", info[n2]['title'], "(", n2, ")"

    if True:
        print "喜欢：武侠(4942776)"
        print "不喜欢: 三傻大佬宝莱坞(3793023)"
        n2 = b.recommend(dict([(4942776L, 0), (3793023L, 1)]))
        print "推荐：", info[n2]['title'], "(", n2, ")"

    if True:
        print "喜欢：龙门客栈(1459054)"
        print "不喜欢：驴得水(25921812)"
        n2 = b.recommend(dict([(1459054L, 0), (25921812L, 1)]))
        print "推荐：", info[n2]['title'], "(", n2, ")"

def getUserInfo(data):
    temp = {}
    for uid, pid, rate in data:
        if uid not in temp:
            temp[uid] = []
        temp[uid].append((pid, 0 if rate >= 3 else 1))

    return temp

def validation(allActions, b, uidInfo):
    count = 0
    rightCount = 0
    errCount = 0
    randomCount = 0

    for uid, pid, act in allActions:
        isLike = 0 if act >= 3 else 1 
        r = b.predict(uidInfo.get(uid, {}), pid)
        if r >= 0:
            count += 1
            if r == isLike:
                rightCount += 1

            randomPredict = random.choice([0,1])
            if randomPredict == isLike:
                randomCount += 1
        else:
            errCount += 1

    print count, rightCount, errCount, randomCount
    print rightCount*1.0/count
    print randomCount*1.0/count

def alsValidation(allActions, b):
    count = 0
    errCount = 0
    randomCount = 0
    sumE = 0.0
    sumRE = 0.0

    for uid, pid, act in allActions:
        r = b.predict(uid, pid)
        if r != None:
            r /= 100
            count += 1
            sumE += 1.0 * (act - r) * (act - r)

            randomPredict = random.choice([0,1,2,3,4,5])
            sumRE += 1.0 * (act - randomPredict) * (act - randomPredict)
            print act, r, randomPredict
        else:
            errCount += 1

    sumE = sqrt(sumE/count)
    sumRE = sqrt(sumRE/count)
    print count, errCount
    print sumE
    print sumRE

if __name__ == "__main__":

    host = config.db['host']
    user = config.db['user']
    passwd = config.db['passwd']

    if len(sys.argv) > 2 and sys.argv[2] == "test1":
        info = getMoviesInfo(host, user, passwd)
        if sys.argv[1] == "bayes":
            trainData = getUserBehavior(host, user, passwd)
            engine = BayesEngine(trainData, info)
            test1(engine, info)
        elif sys.argv[1] == "als":
            df, plays = read_data(host, user, passwd)
            engine = ALSEngine(df, plays)
            test1(engine, info)
        elif sys.argv[1] == "lsi":
            engine = LSIEngine(readItemInfos(host, user, passwd))
            test1(engine, info)
        else:
            print "unknow"
    else:
        data = getUserBehavior(host, user, passwd)
        randomIndex = range(len(data))
        random.shuffle(randomIndex)
        splitIndex = int(round(len(data) * (9/10.0)))
        trainData = [data[index] for index in randomIndex[:splitIndex]]
        testData = [data[index] for index in randomIndex[splitIndex:]]

        if sys.argv[1] == "bayes":
            b = BayesEngine(trainData, getMoviesInfo(host, user, passwd))
            validation(testData, b, getUserInfo(trainData))
        elif sys.argv[1] == "als":
            #df, plays = read_data(host, user, passwd)

            user, artist, plays = zip(*trainData)

            data = DataFrame({"user":user, "artist":artist, "plays":plays})
            data['plays'] *= 100

            # map each artist and user to a unique numeric value
            data['user'] = data['user'].astype("category")
            data['artist'] = data['artist'].astype("category")
            # create a sparse matrix of all the users/plays
            plays = coo_matrix((data['plays'].astype(float),
                               (data['artist'].cat.codes.copy(),
                                data['user'].cat.codes.copy())))

            engine = ALSEngine(data, plays)
            alsValidation(testData, engine)
        elif sys.argv[1] == "lsi":
            #engine = LSIEngine(readItemInfos(host, user, passwd))
            pass
        else:
            print "unknow"

