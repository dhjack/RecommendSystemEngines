#! /usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import random
import json
import numpy as np

class BayesEngine():
    '''
    P (喜欢节目A|用户看过了节目a,b,c) = P (用户看过的节目a,b,c|喜欢节目A) * P (喜欢节目A) / P (用户看过节目a,b,c)
    P (用户看过的节目a,b,c|喜欢节目A) = P (用户看过节目a|喜欢节目A) * P (用户看过节目b|喜欢节目A) * P (用户看过节目c|喜欢节目A)
    P (用户看过节目a|喜欢节目A) = count(喜欢节目A的用户中，看过节目a的用户数) / count(喜欢节目A的用户数)
    P (喜欢节目A) = count(喜欢节目A的用户数) / count(总用户数)

    P (喜欢节目A|用户喜欢节目a,不喜欢节目b) = P (用户喜欢节目a,不喜欢节目b|喜欢节目A) * P (喜欢节目A) / P (用户喜欢节目a,不喜欢节目b)
    P (用户喜欢节目a,不喜欢节目b|喜欢节目A) = P (用户喜欢节目a|喜欢节目A) * P (用户不喜欢节目b|喜欢节目A)
    P (用户喜欢节目a|喜欢节目A) = count(喜欢节目A的用户中，喜欢节目a的用户数) / count(喜欢节目A的用户数)
    P (用户不喜欢节目b|喜欢节目A) = count(喜欢节目A的用户中，不喜欢节目b的用户数) / count(喜欢节目A的用户数)
    P (喜欢节目A) = count(喜欢节目A的用户数) / count(总用户数)

    P (不喜欢节目A|用户喜欢节目a,不喜欢节目b) = P (用户喜欢节目a,不喜欢节目b|不喜欢节目A) * P (不喜欢节目A) / P (用户喜欢节目a,不喜欢节目b)
    P (用户喜欢节目a,不喜欢节目b|不喜欢节目A) = P (用户喜欢节目a|不喜欢节目A) * P (用户不喜欢节目b|不喜欢节目A)
    P (用户喜欢节目a|不喜欢节目A) = count(不喜欢节目A的用户中，喜欢节目a的用户数) / count(不喜欢节目A的用户数)
    P (用户不喜欢节目b|不喜欢节目A) = count(不喜欢节目A的用户中，不喜欢节目b的用户数) / count(不喜欢节目A的用户数)
    P (喜欢节目A) = count(喜欢节目A的用户数) / count(总用户数)
    '''

    def __init__(self, behaviors, moviesInfo):
        '''
        behaviors: (user, item, score)
        uidInfo: (user, set[watched])
        pidInfo: (pid, (set[favorite item], set[unfavorite item]))
        '''
        self.uidInfo, self.pidInfo = self.storeBehavior(behaviors)
        self.moviesInfo = moviesInfo

        self.sortedInfo = zip(*sorted(self.moviesInfo.items(), key=lambda x:x[1]['rating']['average'], reverse=True)[:100])[0]
        #print self.sortedInfo

        print "init finish"

    def storeBehavior(self, data):
        uidInfo = {}
        pidInfo = {}
        for uid, pid, rate in data:
            pid = long(pid)
            rate = int(rate)
            if uid not in uidInfo:
                uidInfo[uid] = set()
            uidInfo[uid].add(pid)

            if pid not in pidInfo:
                pidInfo[pid] = [set(), set()]
            if rate >= 3:
                pidInfo[pid][0].add(uid)
            else:
                pidInfo[pid][1].add(uid)

        return (uidInfo, pidInfo)

    def recommend(self, actions):
        if len(actions) == 0:
            return np.random.choice(self.sortedInfo)
        else:
            return self.recommendByAction(actions, self.uidInfo, self.pidInfo)

    def recommendByActionOld(self, actions, uidInfo, pidInfo):
        '''
        actions: like {pid:0, pid:1}, 0 is like and 1 is not like
        uidInfo: (user, set[watched])
        pidInfo: (pid, (set[favorite useid], set[unfavorite useid]))
        '''
        recommendPid = 0L
        oldProbability = -1
        # 遍历所有节目，计算对应的分值，取最大者
        for pid, info in pidInfo.iteritems():
            if pid in actions or len(info[0]) == 0:
                continue
            pm = len(info[0]) * 1.0 / len(uidInfo)
            pa = 1.0
            for watchedPid, act in actions.iteritems():
                paN = len(pidInfo.get(watchedPid, [set(), set()])[act] & info[0]) * 1.0 / len(info[0])

                #print "paN", paN
                # 如果没有数据，默认给一个初始值
                if paN == 0.0:
                    pa *= 0.001
                else:
                    pa *= paN
                
            newProbability = pm * pa
            if newProbability > oldProbability:
                oldProbability = newProbability
                recommendPid = pid

        return recommendPid

    def recommendByAction(self, actions, uidInfo, pidInfo):
        '''
        actions: like {pid:0, pid:1}, 0 is like and 1 is not like
        uidInfo: (user, set[watched])
        pidInfo: (pid, (set[favorite useid], set[unfavorite useid]))
        '''
        recommendPid = 0L
        oldProbability = -1
        totalUserCount = len(uidInfo)
        # 遍历所有节目，计算喜欢的概率和不喜欢的概率。取差值?还是极大值?
        for pid, info in pidInfo.iteritems():
            if pid in actions:
                continue
            likeUserCount = len(info[0]) + 1.0
            unlikeUserCount = len(info[1]) + 1.0
            likeProbability = 0.0
            unlikeProbability = 0.0
            pa = 1.0
            pb = 1.0
            for watchedPid, act in actions.iteritems():
                # 如果没有数据，默认给一个初始值
                currentActUsers = pidInfo.get(watchedPid, [set(), set()])[act] 
                pa *= len(currentActUsers & info[0]) * 1.0 / likeUserCount + 0.0001
                pb *= len(currentActUsers & info[1]) * 1.0 / unlikeUserCount + 0.0001

            likeProbability = (likeUserCount / totalUserCount) * pa
            unlikeProbability = (unlikeUserCount / totalUserCount) * pb

            if likeProbability > unlikeProbability and likeProbability > oldProbability:
                oldProbability = likeProbability
                recommendPid = pid

        #print "probability:", oldProbability
        return recommendPid
    
    def predict(self, actions, pid):
        totalUserCount = len(self.uidInfo)
        if pid not in self.pidInfo:
            print "Error. %d is not valid pid in pidInfo" % (pid)
            return -1

        info = self.pidInfo[pid]
        likeUserCount = len(info[0]) + 1.0
        unlikeUserCount = len(info[1]) + 1.0
        likeProbability = 0.0
        unlikeProbability = 0.0
        pa = 1.0
        pb = 1.0
        for watchedPid, act in actions:
            # 如果没有数据，默认给一个初始值
            currentActUsers = self.pidInfo.get(watchedPid, [set(), set()])[act] 
            pa *= len(currentActUsers & info[0]) * 1.0 / likeUserCount + 0.0001
            pb *= len(currentActUsers & info[1]) * 1.0 / unlikeUserCount + 0.0001

        likeProbability = (likeUserCount / totalUserCount) * pa
        unlikeProbability = (unlikeUserCount / totalUserCount) * pb

        if likeProbability > unlikeProbability:
            return 0
        else :
            return 1

def getUserBehavior(host, user, passwd):
    db = MySQLdb.connect(host, user, passwd, "reSystem", charset="utf8")
    cursor = db.cursor()      
    cursor.execute("SET NAMES 'utf8'")
    cursor.execute("select uid, pid, rate from userRates")
    data = cursor.fetchall()
    db.close()
    return data

def getMoviesInfo(host, user, passwd):
    db = MySQLdb.connect(host, user, passwd, "reSystem", charset="utf8")
    cursor = db.cursor()      
    cursor.execute("SET NAMES 'utf8'")

    cursor.execute("select * from moviesJsonInfo")
    data = cursor.fetchall()

    moviesInfo = {}
    for pid, info in data:
        moviesInfo[pid] = json.loads(info, strict=False)

    db.close()
    return moviesInfo

def getOneUserBehavior(host, user, passwd):
    db = MySQLdb.connect(host, user, passwd, "reSystem", charset="utf8")
    cursor = db.cursor()      
    cursor.execute("SET NAMES 'utf8'")
    #cursor.execute("select uid, pid, rate from userRates where pid != 25934014")
    cursor.execute("select uid, pid, rate from userRates")
    data = cursor.fetchall()
    db.close()

    actions = {}
    for uid, pid, rate in data:
        if uid not in actions:
            actions[uid] = []
        actions[uid].append((pid, 0 if rate >= 3 else 1))
    return actions

def corssValidation(allActions, b):
    for i in range(3):
        testData = {}
        count = 0
        rightCount = 0
        errCount = 0
        randomCount = 0
        for uid, act in allActions.iteritems():
            randomIndex = range(len(act))
            random.shuffle(randomIndex)
            splitIndex = int(round(len(act) * (3/5.0)))
            testData[uid] = ([act[index] for index in randomIndex[:splitIndex]],
                    [act[index] for index in randomIndex[splitIndex:]])

        for uid, (trains, tests) in testData.iteritems():
            for pid, isLike in tests:
                r = b.predict(trains, pid)
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

def getUserInfo(data):
    temp = {}
    for uid, pid, rate in data:
        if uid not in temp:
            temp[uid] = []
        temp[uid].append((pid, 0 if rate >= 3 else 1))

    return temp


if __name__ == "__main__":
    import config
    host = config.db['host']
    user = config.db['user']
    passwd = config.db['passwd']

    data = getUserBehavior(host, user, passwd)
    randomIndex = range(len(data))
    random.shuffle(randomIndex)
    splitIndex = int(round(len(data) * (4/5.0)))
    trainData = [data[index] for index in randomIndex[:splitIndex]]
    testData = [data[index] for index in randomIndex[splitIndex:]]

    b = BayesEngine(trainData, getMoviesInfo(host, user, passwd))
    validation(testData, b, getUserInfo(trainData))

    #uidInfo = dict([("a", (103, 105)),("b", (103, 104)),("c", (104))])
    #pidInfo = dict([(103, (set(["a", "b"]), set())),(104, (set(["c", "b"]), set(["a"]))),(105, (set(["a"]), set(["c"])))])

    #info = getMoviesInfo(host, user, passwd)
    #allActions = getOneUserBehavior(host, user, passwd)

    #n1 = b.recommend(dict())
    #print n1
    #print info[n1]['title']
#    if False:
#        for uid, v in allActions.iteritems():
#            n2 = b.recommend(dict(v))
#            temp = { 0 : [], 1 : []}
#            for n1, isLike in v:
#                if n1 in info:
#                    temp[isLike].append(info[n1]['title'])
#                else:
#                    print "Error key" , n1
#
#            print "喜欢：", " | ".join(temp[0])
#            print "不喜欢：", " | ".join(temp[1])
#
#            print "推荐"
#            print n2
#            print info[n2]['title'] if n2 in info else n2
#    if False:
#        #黑客帝国(1291843) 源代码(3075287)
#        n2 = b.recommend(dict([(1291843L, 0), (3075287L, 0), (20326557L, 1), (3319755L, 1)]))
#        print n2
#        print info[n2]['title']
#
#    if False:
#        #巴黎圣母院(20326557) 怦然心动(3319755)
#        n2 = b.recommend(dict([(20326557L, 0), (3319755L, 0)]))
#        print n2
#        print info[n2]['title']
#
#    if False:
#        #这个杀手不太冷(1295644) 英雄本色(1297574)
#        n2 = b.recommend(dict([(1295644L, 0), (1297574L, 0)]))
#        print n2
#        print info[n2]['title']
#
#    if False:
#        #疯狂动物城(25662329)   三傻大佬宝莱坞(3793023)
#        n2 = b.recommend(dict([(25662329L, 0), (3793023L, 0)]))
#        print n2
#        print info[n2]['title']
#
#    if False:
#        #新龙门客栈(1292287) 卧虎藏龙(1301168)
#        n2 = b.recommend(dict([(1292287L, 0), (1301168L, 0)]))
#        print n2
#        print info[n2]['title']
    #print recommendByAction([(103, 1)], uidInfo, pidInfo)
    #print recommendByAction(dict([(105, 0)]), uidInfo, pidInfo)
