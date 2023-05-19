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

#include "tsdbDef.h"

#ifndef _TSDB_FILE_H
#define _TSDB_FILE_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct STFile    STFile;
typedef struct STFileObj STFileObj;

typedef enum {
  TSDB_FTYPE_HEAD = 0,                   // .head
  TSDB_FTYPE_DATA,                       // .data
  TSDB_FTYPE_SMA,                        // .sma
  TSDB_FTYPE_TOMB,                       // .tomb
  TSDB_FTYPE_STT = TSDB_FTYPE_TOMB + 2,  // .stt
} tsdb_ftype_t;

#define TSDB_FTYPE_MIN TSDB_FTYPE_HEAD
#define TSDB_FTYPE_MAX (TSDB_FTYPE_TOMB + 1)

// STFile
int32_t tsdbTFileInit(STsdb *pTsdb, STFile *pFile);
int32_t tsdbTFileClear(STFile *pFile);
int32_t tsdbTFileToJson(const STFile *f, cJSON *json);
int32_t tsdbJsonToTFile(const cJSON *json, tsdb_ftype_t ftype, STFile *f);

// STFileObj
int32_t tsdbTFileObjCreate(const STFile *f, STFileObj **fobj);
int32_t tsdbTFileObjDestroy(STFileObj *fobj);

struct STFile {
  char         fname[TSDB_FILENAME_LEN];
  tsdb_ftype_t type;
  SDiskID      did;  // disk id
  int32_t      fid;  // file id
  int64_t      cid;  // commit id
  int64_t      size;
  union {
    struct {
      int32_t level;
      int32_t nseg;
    } stt;
  };
};

struct STFileObj {
  SRBTreeNode      rbtn;
  volatile int32_t ref;
  STFile           f;
};

#ifdef __cplusplus
}
#endif

#endif /*_TSDB_FILE_H*/