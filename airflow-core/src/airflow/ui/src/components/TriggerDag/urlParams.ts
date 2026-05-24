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

import type { DataIntervalMode, TriggerDagPrefillConfig } from "./types";

const isDataIntervalMode = (value: string): value is DataIntervalMode => value === "auto" || value === "manual";

const setKnownPrefillValue = (prefillConfig: TriggerDagPrefillConfig, key: string, value: string): boolean => {
  if (key === "dataIntervalMode" || key === "data_interval_mode") {
    if (isDataIntervalMode(value)) {
      prefillConfig.dataIntervalMode = value;
    }

    return true;
  }

  if (key === "dagRunId" || key === "dag_run_id") {
    prefillConfig.dagRunId = value;

    return true;
  }

  if (key === "dataIntervalEnd" || key === "data_interval_end") {
    prefillConfig.dataIntervalEnd = value;

    return true;
  }

  if (key === "dataIntervalStart" || key === "data_interval_start") {
    prefillConfig.dataIntervalStart = value;

    return true;
  }

  if (key === "logicalDate" || key === "logical_date") {
    prefillConfig.logicalDate = value;

    return true;
  }

  if (key === "note") {
    prefillConfig.note = value;

    return true;
  }

  if (key === "partitionKey" || key === "partition_key") {
    prefillConfig.partitionKey = value;

    return true;
  }

  return false;
};

export const getTriggerDagPrefillConfig = (searchParams: URLSearchParams): TriggerDagPrefillConfig | undefined => {
  const prefillConfig: TriggerDagPrefillConfig = {};
  const conf: Record<string, unknown> = {};

  for (const key of new Set(searchParams.keys())) {
    const values = searchParams.getAll(key);
    const lastValue = values.at(-1);

    if (values.length > 0 && lastValue !== undefined) {
      if (!setKnownPrefillValue(prefillConfig, key, lastValue)) {
        conf[key] = values.length === 1 ? lastValue : values;
      }
    }
  }

  if (Object.keys(conf).length > 0) {
    prefillConfig.conf = conf;
  }

  return Object.keys(prefillConfig).length > 0 ? prefillConfig : undefined;
};
