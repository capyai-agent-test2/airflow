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
import { describe, expect, it } from "vitest";

import { SearchParamsKeys } from "src/constants/searchParams";

import { getTaskInstancesFilterKeys } from "./TaskInstancesFilter.utils";

describe("getTaskInstancesFilterKeys", () => {
  it("uses task name search for the global task instances list", () => {
    const keys = getTaskInstancesFilterKeys({});

    expect(keys).toContain(SearchParamsKeys.NAME_PATTERN);
    expect(keys).toContain(SearchParamsKeys.RENDERED_MAP_INDEX);
    expect(keys.indexOf(SearchParamsKeys.NAME_PATTERN)).toBeLessThan(
      keys.indexOf(SearchParamsKeys.RENDERED_MAP_INDEX),
    );
  });

  it("uses rendered map index search first for mapped task instance lists", () => {
    const keys = getTaskInstancesFilterKeys({
      dagId: "dag",
      runId: "run",
      taskId: "mapped_task",
    });

    expect(keys[0]).toBe(SearchParamsKeys.RENDERED_MAP_INDEX);
    expect(keys).toContain(SearchParamsKeys.NAME_PATTERN);
    expect(keys.indexOf(SearchParamsKeys.RENDERED_MAP_INDEX)).toBeLessThan(
      keys.indexOf(SearchParamsKeys.NAME_PATTERN),
    );
  });
});
