/*
 * Copyright (c) 2019 TAOS Data, Inc. <jhtao@taosdata.com>
 *
 * This program is free software: you can use, redistribute, and/or modify
 * it under the terms of the GNU Affero General Public License, version 3
 * or later ("AGPL"), as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "tsdbFile.h"

#ifndef _TSDB_FILE_SET_H
#define _TSDB_FILE_SET_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct STFileSet STFileSet;
typedef struct STFileOp  STFileOp;
typedef struct SSttLvl   SSttLvl;
typedef TARRAY2(STFileSet *) TFileSetArray;
typedef TARRAY2(SSttLvl *) TSttLvlArray;

typedef enum {
  TSDB_FOP_NONE = 0,
  TSDB_FOP_EXTEND,
  TSDB_FOP_CREATE,
  TSDB_FOP_DELETE,
  TSDB_FOP_TRUNCATE,
} tsdb_fop_t;

int32_t tsdbFileSetInit(int32_t fid, STFileSet **fset);
int32_t tsdbFileSetInitEx(const STFileSet *fset1, STFileSet **fset2);
int32_t tsdbFileSetClear(STFileSet **fset);

int32_t tsdbFileSetToJson(const STFileSet *fset, cJSON *json);
int32_t tsdbJsonToFileSet(const cJSON *json, STFileSet **fset);
int32_t tsdbFileSetEdit(STFileSet *fset, const STFileOp *op);
int32_t tsdbFSetCmprFn(const STFileSet *pSet1, const STFileSet *pSet2);

const SSttLvl *tsdbFileSetGetLvl(const STFileSet *fset, int32_t level);

struct STFileOp {
  tsdb_fop_t op;
  int32_t    fid;
  STFile     oState;  // old file state
  STFile     nState;  // new file state
};

struct SSttLvl {
  int32_t     level;    // level
  int32_t     nstt;     // number of .stt files on this level
  SRBTree     sttTree;  // .stt file tree, sorted by cid
  SRBTreeNode rbtn;
};

struct STFileSet {
  int32_t      fid;
  STFileObj   *farr[TSDB_FTYPE_MAX];  // file array
  TSttLvlArray lvlArr;                // level array
};

#ifdef __cplusplus
}
#endif

#endif /*_TSDB_FILE_SET_H*/