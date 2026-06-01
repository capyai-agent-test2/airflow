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
import { VStack } from "@chakra-ui/react";
import { useSearchParams, useParams } from "react-router-dom";

import { FilterBar, type FilterValue } from "src/components/FilterBar";
import { useFiltersHandler } from "src/utils";

import { getTaskInstancesFilterKeys } from "./TaskInstancesFilter.utils";

export const TaskInstancesFilter = () => {
  const { dagId, runId, taskId } = useParams();
  const paramKeys = getTaskInstancesFilterKeys({ dagId, runId, taskId });

  const [searchParams] = useSearchParams();

  const { filterConfigs, handleFiltersChange } = useFiltersHandler(paramKeys);

  const initialValues: Record<string, FilterValue> = {};

  filterConfigs.forEach((config) => {
    const value = searchParams.get(config.key);

    if (value !== null && value !== "") {
      if (config.type === "number") {
        const parsedValue = Number(value);

        initialValues[config.key] = isNaN(parsedValue) ? value : parsedValue;
      } else {
        initialValues[config.key] = value;
      }
    }
  });

  return (
    <VStack align="start" justifyContent="space-between">
      <VStack alignItems="flex-start" gap={1}>
        <FilterBar
          configs={filterConfigs}
          initialValues={initialValues}
          onFiltersChange={handleFiltersChange}
        />
      </VStack>
    </VStack>
  );
};
