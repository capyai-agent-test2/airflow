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

import { buildDagNavigationPath, buildRunNavigationPath } from "./dagNavigation";

describe("buildDagNavigationPath", () => {
  it.each([
    ["/dags/source_dag/code", "/dags/target_dag/code"],
    ["/dags/source_dag/runs/run_1/events", "/dags/target_dag/events"],
    ["/dags/source_dag/runs/run_1/details", "/dags/target_dag/details"],
    ["/dags/source_dag/runs/run_1/asset_events", "/dags/target_dag"],
    ["/dags/source_dag", "/dags/target_dag"],
  ])("builds a Dag path from %s", (pathname, expected) => {
    expect(buildDagNavigationPath({ dagId: "target_dag", pathname })).toBe(expected);
  });
});

describe("buildRunNavigationPath", () => {
  it.each([
    ["/dags/test_dag/runs/run_1/events", "/dags/test_dag/runs/run_2/events"],
    ["/dags/test_dag/runs/run_1/details", "/dags/test_dag/runs/run_2/details"],
    ["/dags/test_dag/runs/run_1", "/dags/test_dag/runs/run_2"],
  ])("preserves compatible Dag run tabs from %s", (pathname, expected) => {
    expect(buildRunNavigationPath({ dagId: "test_dag", pathname, runId: "run_2" })).toBe(expected);
  });

  it("keeps the task path when changing Dag runs from a task selection", () => {
    expect(
      buildRunNavigationPath({
        dagId: "test_dag",
        pathname: "/dags/test_dag/runs/run_1/tasks/task_1",
        runId: "run_2",
        taskId: "task_1",
      }),
    ).toBe("/dags/test_dag/runs/run_2/tasks/task_1");
  });
});
