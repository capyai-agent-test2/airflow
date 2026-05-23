/*!
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { useParams } from "react-router-dom";

import { useGridServiceGetGridRuns } from "openapi/queries";
import type { DagRunState, DagRunType } from "openapi/requests/types.gen";
import { isStatePending, useAutoRefresh } from "src/utils";

export const useGridRuns = ({
  bundleVersion,
  confContains,
  consumingAssetPattern,
  dagRunState,
  dagVersion,
  durationGte,
  durationLte,
  endDateGte,
  endDateLte,
  limit,
  logicalDateGte,
  logicalDateLte,
  offset,
  runAfterGte,
  runAfterLte,
  runType,
  startDateGte,
  startDateLte,
  triggeringUser,
}: {
  bundleVersion?: string;
  confContains?: string;
  consumingAssetPattern?: string;
  dagVersion?: number;
  durationGte?: number;
  durationLte?: number;
  endDateGte?: string;
  endDateLte?: string;
  dagRunState?: DagRunState | undefined;
  limit: number;
  logicalDateGte?: string;
  logicalDateLte?: string;
  offset?: number;
  runAfterGte?: string;
  runAfterLte?: string;
  runType?: DagRunType | undefined;
  startDateGte?: string;
  startDateLte?: string;
  triggeringUser?: string | undefined;
}) => {
  const { dagId = "" } = useParams();

  const refetchInterval = useAutoRefresh({ dagId });

  const { data: GridRuns, ...rest } = useGridServiceGetGridRuns(
    {
      bundleVersion: bundleVersion ?? undefined,
      confContains: confContains ?? undefined,
      consumingAssetPattern: consumingAssetPattern ?? undefined,
      dagId,
      dagVersion: dagVersion === undefined ? undefined : [dagVersion],
      durationGte,
      durationLte,
      endDateGte: endDateGte ?? undefined,
      endDateLte: endDateLte ?? undefined,
      limit,
      logicalDateGte: logicalDateGte ?? undefined,
      logicalDateLte: logicalDateLte ?? undefined,
      offset: offset ?? undefined,
      orderBy: ["-run_after"],
      runAfterGte: runAfterGte ?? undefined,
      runAfterLte: runAfterLte ?? undefined,
      runType: runType ? [runType] : undefined,
      startDateGte: startDateGte ?? undefined,
      startDateLte: startDateLte ?? undefined,
      state: dagRunState ? [dagRunState] : undefined,
      triggeringUser: triggeringUser ?? undefined,
    },
    undefined,
    {
      placeholderData: (prev) => prev,
      refetchInterval: (query) =>
        query.state.data?.some((run) => isStatePending(run.state)) && refetchInterval,
    },
  );

  return { data: GridRuns, ...rest };
};
