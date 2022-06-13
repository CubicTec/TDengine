#include "syncRaftStore.h"
//#include <gtest/gtest.h>
#include <stdio.h>
#include "syncIO.h"
#include "syncInt.h"
#include "syncRaftCfg.h"
#include "syncUtil.h"

void logTest() {
  sTrace("--- sync log test: trace");
  sDebug("--- sync log test: debug");
  sInfo("--- sync log test: info");
  sWarn("--- sync log test: warn");
  sError("--- sync log test: error");
  sFatal("--- sync log test: fatal");
}

SRaftCfg* createRaftCfg() {
  SRaftCfg* pCfg = (SRaftCfg*)taosMemoryMalloc(sizeof(SRaftCfg));
  memset(pCfg, 0, sizeof(SRaftCfg));

  pCfg->cfg.replicaNum = 3;
  pCfg->cfg.myIndex = 1;
  for (int i = 0; i < pCfg->cfg.replicaNum; ++i) {
    ((pCfg->cfg.nodeInfo)[i]).nodePort = i * 100;
    snprintf(((pCfg->cfg.nodeInfo)[i]).nodeFqdn, sizeof(((pCfg->cfg.nodeInfo)[i]).nodeFqdn), "100.200.300.%d", i);
  }
  pCfg->isStandBy = taosGetTimestampSec() % 100;

  return pCfg;
}

SSyncCfg* createSyncCfg() {
  SSyncCfg* pCfg = (SSyncCfg*)taosMemoryMalloc(sizeof(SSyncCfg));
  memset(pCfg, 0, sizeof(SSyncCfg));

  pCfg->replicaNum = 3;
  pCfg->myIndex = 1;
  for (int i = 0; i < pCfg->replicaNum; ++i) {
    ((pCfg->nodeInfo)[i]).nodePort = i * 100;
    snprintf(((pCfg->nodeInfo)[i]).nodeFqdn, sizeof(((pCfg->nodeInfo)[i]).nodeFqdn), "100.200.300.%d", i);
  }

  return pCfg;
}

void test1() {
  SSyncCfg* pCfg = createSyncCfg();
  syncCfgLog2((char*)__FUNCTION__, pCfg);
  taosMemoryFree(pCfg);
}

void test2() {
  SSyncCfg* pCfg = createSyncCfg();
  char*     s = syncCfg2Str(pCfg);

  SSyncCfg* pCfg2 = (SSyncCfg*)taosMemoryMalloc(sizeof(SSyncCfg));
  int32_t   ret = syncCfgFromStr(s, pCfg2);
  assert(ret == 0);
  syncCfgLog2((char*)__FUNCTION__, pCfg2);

  taosMemoryFree(pCfg);
  taosMemoryFree(s);
  taosMemoryFree(pCfg2);
}

void test3() {
  SSyncCfg* pCfg = createSyncCfg();
  char*     s = (char*)"./test3_raft_cfg.json";

  if (taosCheckExistFile(s)) {
    printf("%s file: %s already exist! \n", (char*)__FUNCTION__, s);
  } else {
    SRaftCfgMeta meta;
    meta.isStandBy = 7;
    meta.snapshotEnable = 9;
    meta.lastConfigIndex = 789;
    raftCfgCreateFile(pCfg, meta, s);
    printf("%s create json file: %s \n", (char*)__FUNCTION__, s);
  }

  taosMemoryFree(pCfg);
}

void test4() {
  SRaftCfg* pCfg = raftCfgOpen("./test3_raft_cfg.json");
  assert(pCfg != NULL);

  raftCfgLog2((char*)__FUNCTION__, pCfg);

  int32_t ret = raftCfgClose(pCfg);
  assert(ret == 0);
}

void test5() {
  SRaftCfg* pCfg = raftCfgOpen("./test3_raft_cfg.json");
  assert(pCfg != NULL);

  pCfg->cfg.myIndex = taosGetTimestampSec();
  pCfg->isStandBy += 2;
  pCfg->snapshotEnable += 3;
  pCfg->lastConfigIndex += 1000;
  raftCfgPersist(pCfg);

  printf("%s update json file: %s myIndex->%d \n", (char*)__FUNCTION__, "./test3_raft_cfg.json", pCfg->cfg.myIndex);

  int32_t ret = raftCfgClose(pCfg);
  assert(ret == 0);
}

int main() {
  tsAsyncLog = 0;
  sDebugFlag = DEBUG_TRACE + DEBUG_SCREEN + DEBUG_FILE;

  logTest();
  test1();
  test2();
  test3();
  test4();
  test5();

  return 0;
}
