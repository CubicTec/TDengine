
import taos
import sys
import time
import socket
import os
import threading

from util.log import *
from util.sql import *
from util.cases import *
from util.dnodes import *
from util.common import *
sys.path.append("./7-tmq")
from tmqCommon import *

class TDTestCase:
    def init(self, conn, logSql):
        tdLog.debug(f"start to excute {__file__}")
        tdSql.init(conn.cursor())
        #tdSql.init(conn.cursor(), logSql)  # output sql.txt file

    def tmqCase1(self):
        tdLog.printNoPrefix("======== test case 1: ")
        paraDict = {'dbName':     'db1',
                    'dropFlag':   1,
                    'event':      '',
                    'vgroups':    4,
                    'stbName':    'stb',
                    'colPrefix':  'c',
                    'tagPrefix':  't',
                    'colSchema':   [{'type': 'INT', 'count':1}, {'type': 'binary', 'len':20, 'count':1}],
                    'tagSchema':   [{'type': 'INT', 'count':1}, {'type': 'binary', 'len':20, 'count':1}],
                    'ctbPrefix':  'ctb',
                    'ctbNum':     10,
                    'rowsPerTbl': 10000,
                    'batchNum':   100,
                    'startTs':    1640966400000,  # 2022-01-01 00:00:00.000
                    'pollDelay':  10,
                    'showMsg':    1,
                    'showRow':    1}

        topicNameList = ['topic1', 'topic2', 'topic3']
        expectRowsList = []
        tmqCom.initConsumerTable()
        tdCom.create_database(tdSql, paraDict["dbName"],paraDict["dropFlag"], vgroups=4,replica=1)
        tdLog.info("create stb")
        tdCom.create_stable(tdSql, dbname=paraDict["dbName"],stbname=paraDict["stbName"], column_elm_list=paraDict['colSchema'], tag_elm_list=paraDict['tagSchema'])
        tdLog.info("create ctb")
        tdCom.create_ctable(tdSql, dbname=paraDict["dbName"],stbname=paraDict["stbName"],tag_elm_list=paraDict['tagSchema'],count=paraDict["ctbNum"], default_ctbname_prefix=paraDict['ctbPrefix'])
        tdLog.info("insert data")
        tmqCom.insert_data(tdSql,paraDict["dbName"],paraDict["ctbPrefix"],paraDict["ctbNum"],paraDict["rowsPerTbl"],paraDict["batchNum"],paraDict["startTs"])
        
        tdLog.info("create topics from stb with filter")
        tdSql.execute("create topic %s as select ts, c1, c2 from %s.%s where c1 %% 4 == 0" %(topicNameList[0], paraDict['dbName'], paraDict['stbName']))
        expectRowsList.append(paraDict["rowsPerTbl"] * paraDict["ctbNum"] / 4)

        tdSql.execute("create topic %s as select ts, c1, c2 from %s.%s where c1 >= 5000" %(topicNameList[1], paraDict['dbName'], paraDict['stbName']))
        expectRowsList.append(paraDict["rowsPerTbl"] * paraDict["ctbNum"] / 2)

        sqlString = "create topic %s as select ts, c1, c2 from %s.%s where ts >= %d" %(topicNameList[2], paraDict['dbName'], paraDict['stbName'], paraDict["startTs"]+9000)
        print(sqlString)
        tdSql.execute(sqlString)
        # tdSql.execute("create topic %s as select ts, c1, c2 from %s.%s where ts >= %d" %(topicNameList[2], paraDict['dbName'], paraDict['stbName'], paraDict["startTs"]+9000))
        expectRowsList.append(paraDict["rowsPerTbl"] * paraDict["ctbNum"] / 10)

        tdLog.info("insert consume info to consume processor")
        consumerId   = 0
        expectrowcnt = paraDict["rowsPerTbl"] * paraDict["ctbNum"]
        topicList    = topicNameList[0]
        ifcheckdata  = 0
        ifManualCommit = 1
        keyList      = 'group.id:cgrp1, enable.auto.commit:false, auto.commit.interval.ms:6000, auto.offset.reset:earliest'
        tmqCom.insertConsumerInfo(consumerId, expectrowcnt,topicList,keyList,ifcheckdata,ifManualCommit)

        tdLog.info("start consume processor")
        tmqCom.startTmqSimProcess(paraDict['pollDelay'],paraDict["dbName"],paraDict['showMsg'], paraDict['showRow'])

        tdLog.info("wait the consume result") 
        expectRows = 1
        resultList = tmqCom.selectConsumeResult(expectRows)
        
        if expectRowsList[0] != resultList[0]:
            tdLog.info("expect consume rows: %d, act consume rows: %d"%(expectRowsList[0], resultList[0]))
            tdLog.exit("0 tmq consume rows error!")

        # reinit consume info, and start tmq_sim, then check consume result
        tmqCom.initConsumerTable()
        consumerId   = 1
        topicList    = topicNameList[1]
        tmqCom.insertConsumerInfo(consumerId, expectrowcnt,topicList,keyList,ifcheckdata,ifManualCommit)

        tdLog.info("start consume processor")
        tmqCom.startTmqSimProcess(paraDict['pollDelay'],paraDict["dbName"],paraDict['showMsg'], paraDict['showRow'])

        tdLog.info("wait the consume result") 
        expectRows = 1
        resultList = tmqCom.selectConsumeResult(expectRows)
        if expectRowsList[1] != resultList[0]:
            tdLog.info("expect consume rows: %d, act consume rows: %d"%(expectRowsList[1], resultList[0]))
            tdLog.exit("1 tmq consume rows error!")

        # reinit consume info, and start tmq_sim, then check consume result
        tmqCom.initConsumerTable()
        consumerId   = 2
        topicList    = topicNameList[2]
        tmqCom.insertConsumerInfo(consumerId, expectrowcnt,topicList,keyList,ifcheckdata,ifManualCommit)

        tdLog.info("start consume processor")
        tmqCom.startTmqSimProcess(paraDict['pollDelay'],paraDict["dbName"],paraDict['showMsg'], paraDict['showRow'])

        tdLog.info("wait the consume result") 
        expectRows = 1
        resultList = tmqCom.selectConsumeResult(expectRows)
        if expectRowsList[2] != resultList[0]:
            tdLog.info("expect consume rows: %d, act consume rows: %d"%(expectRowsList[2], resultList[0]))
            tdLog.exit("2 tmq consume rows error!")

        time.sleep(10)        
        for i in range(len(topicNameList)):
            tdSql.query("drop topic %s"%topicNameList[i])

        tdLog.printNoPrefix("======== test case 1 end ...... ")

    def tmqCase2(self):
        tdLog.printNoPrefix("======== test case 2: ")
        paraDict = {'dbName':     'db2',
                    'dropFlag':   1,
                    'event':      '',
                    'vgroups':    4,
                    'stbName':    'stb',
                    'colPrefix':  'c',
                    'tagPrefix':  't',
                    'colSchema':   [{'type': 'INT', 'count':2}, {'type': 'binary', 'len':20, 'count':1}],
                    'tagSchema':   [{'type': 'INT', 'count':1}, {'type': 'binary', 'len':20, 'count':1}],
                    'ctbPrefix':  'ctb',
                    'ctbNum':     10,
                    'rowsPerTbl': 10000,
                    'batchNum':   100,
                    'startTs':    1640966400000,  # 2022-01-01 00:00:00.000
                    'pollDelay':  10,
                    'showMsg':    1,
                    'showRow':    1}

        topicNameList = ['topic1', 'topic2', 'topic3']
        expectRowsList = []
        tmqCom.initConsumerTable()
        tdCom.create_database(tdSql, paraDict["dbName"],paraDict["dropFlag"], vgroups=4,replica=1)
        tdLog.info("create stb")
        tdCom.create_stable(tdSql, dbname=paraDict["dbName"],stbname=paraDict["stbName"], column_elm_list=paraDict['colSchema'], tag_elm_list=paraDict['tagSchema'])
        tdLog.info("create ctb")
        tmqCom.create_ctable(tdSql, dbName=paraDict["dbName"],stbName=paraDict["stbName"],ctbPrefix=paraDict['ctbPrefix'], ctbNum=paraDict['ctbNum'])
        tdLog.info("insert data")
        tmqCom.insert_data_1(tdSql,paraDict["dbName"],paraDict["ctbPrefix"],paraDict["ctbNum"],paraDict["rowsPerTbl"],paraDict["batchNum"],paraDict["startTs"])

        tdLog.info("create topics from stb with filter")
        # sqlString = "create topic %s as select ts, sin(c1), pow(c2,3) from %s.%s where c2 >= 0" %(topicNameList[0], paraDict['dbName'], paraDict['stbName'])
        queryString = "select ts, sin(c1), pow(c2,3) from %s.%s where c2 >= 0" %(paraDict['dbName'], paraDict['stbName'])
        sqlString = "create topic %s as %s" %(topicNameList[0], queryString)
        tdLog.info("create topic sql: %s"%sqlString)
        tdSql.execute(sqlString)
        tdSql.query(queryString)        
        expectRowsList.append(tdSql.getRows())

        queryString = "select ts, sin(c1), pow(c2,3) from %s.%s where sin(c2) >= 0" %(paraDict['dbName'], paraDict['stbName'])
        sqlString = "create topic %s as %s" %(topicNameList[1], queryString)
        tdLog.info("create topic sql: %s"%sqlString)
        tdSql.execute(sqlString)
        tdSql.query(queryString)
        expectRowsList.append(tdSql.getRows())

        queryString = "select ts, sin(c1), floor(pow(c2,3)), c2 from %s.%s where (sin(c2) >= 0) and (floor(pow(c2,3)) %% 9 == 0)" %(paraDict['dbName'], paraDict['stbName'])
        sqlString = "create topic %s as %s" %(topicNameList[2], queryString)
        tdLog.info("create topic sql: %s"%sqlString)
        tdSql.execute(sqlString)
        tdSql.query(queryString)
        expectRowsList.append(tdSql.getRows())
  
        # start tmq consume processor
        tdLog.info("insert consume info to consume processor")
        consumerId   = 0
        expectrowcnt = paraDict["rowsPerTbl"] * paraDict["ctbNum"]
        topicList    = topicNameList[0]
        ifcheckdata  = 0
        ifManualCommit = 1
        keyList      = 'group.id:cgrp1, enable.auto.commit:false, auto.commit.interval.ms:6000, auto.offset.reset:earliest'
        tmqCom.insertConsumerInfo(consumerId, expectrowcnt,topicList,keyList,ifcheckdata,ifManualCommit)

        tdLog.info("start consume processor")
        tmqCom.startTmqSimProcess(paraDict['pollDelay'],paraDict["dbName"],paraDict['showMsg'], paraDict['showRow'])

        tdLog.info("wait the consume result") 
        expectRows = 1
        resultList = tmqCom.selectConsumeResult(expectRows)
        
        if expectRowsList[0] != resultList[0]:
            tdLog.info("expect consume rows: %d, act consume rows: %d"%(expectRowsList[0], resultList[0]))
            tdLog.exit("0 tmq consume rows error!")

        # reinit consume info, and start tmq_sim, then check consume result
        tmqCom.initConsumerTable()
        consumerId   = 1
        topicList    = topicNameList[1]
        tmqCom.insertConsumerInfo(consumerId, expectrowcnt,topicList,keyList,ifcheckdata,ifManualCommit)

        tdLog.info("start consume processor")
        tmqCom.startTmqSimProcess(paraDict['pollDelay'],paraDict["dbName"],paraDict['showMsg'], paraDict['showRow'])

        tdLog.info("wait the consume result") 
        expectRows = 1
        resultList = tmqCom.selectConsumeResult(expectRows)
        if expectRowsList[1] != resultList[0]:
            tdLog.info("expect consume rows: %d, act consume rows: %d"%(expectRowsList[1], resultList[0]))
            tdLog.exit("1 tmq consume rows error!")

        # # reinit consume info, and start tmq_sim, then check consume result
        tmqCom.initConsumerTable()
        consumerId   = 2
        topicList    = topicNameList[2]
        tmqCom.insertConsumerInfo(consumerId, expectrowcnt,topicList,keyList,ifcheckdata,ifManualCommit)

        tdLog.info("start consume processor")
        tmqCom.startTmqSimProcess(paraDict['pollDelay'],paraDict["dbName"],paraDict['showMsg'], paraDict['showRow'])

        tdLog.info("wait the consume result") 
        expectRows = 1
        resultList = tmqCom.selectConsumeResult(expectRows)
        if expectRowsList[2] != resultList[0]:
            tdLog.info("expect consume rows: %d, act consume rows: %d"%(expectRowsList[2], resultList[0]))
            tdLog.exit("2 tmq consume rows error!")

        # time.sleep(10)        
        # for i in range(len(topicNameList)):
        #     tdSql.query("drop topic %s"%topicNameList[i])

        tdLog.printNoPrefix("======== test case 2 end ...... ")

    def run(self):
        tdSql.prepare()
        # self.tmqCase1()
        self.tmqCase2()

    def stop(self):
        tdSql.close()
        tdLog.success(f"{__file__} successfully executed")

event = threading.Event()

tdCases.addLinux(__file__, TDTestCase())
tdCases.addWindows(__file__, TDTestCase())
