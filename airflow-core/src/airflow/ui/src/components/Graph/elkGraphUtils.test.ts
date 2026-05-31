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

import type { EdgeResponse } from "openapi/requests/types.gen";

import { hasUniformExternalConnectivity } from "./elkGraphUtils";

describe("hasUniformExternalConnectivity", () => {
  it("does not collapse group edges when different children connect to different external sides", () => {
    const childIds = new Set([
      "group.task_a1",
      "group.branch",
      "group.task_a2",
      "group.task_a3",
      "group.done",
    ]);
    const edges: Array<EdgeResponse> = [
      { source_id: "start", target_id: "group.task_a1" },
      { source_id: "group.task_a1", target_id: "group.branch" },
      { source_id: "group.branch", target_id: "group.task_a2" },
      { source_id: "group.branch", target_id: "group.task_a3" },
      { source_id: "group.task_a2", target_id: "group.done" },
      { source_id: "group.task_a3", target_id: "group.done" },
      { source_id: "group.done", target_id: "final" },
      { source_id: "group.task_a2", target_id: "final" },
      { source_id: "group.task_a3", target_id: "final" },
    ];

    expect(hasUniformExternalConnectivity(childIds, edges)).toBe(false);
  });

  it("collapses group edges when externally connected children share the same target", () => {
    const childIds = new Set(["group.task_a", "group.task_b"]);
    const edges: Array<EdgeResponse> = [
      { source_id: "group.task_a", target_id: "final" },
      { source_id: "group.task_b", target_id: "final" },
    ];

    expect(hasUniformExternalConnectivity(childIds, edges)).toBe(true);
  });
});
