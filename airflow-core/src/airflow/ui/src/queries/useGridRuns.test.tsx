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
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useGridRuns } from "./useGridRuns";

const { useGridServiceGetGridRuns } = vi.hoisted(() => ({
  useGridServiceGetGridRuns: vi.fn(() => ({
    data: [],
    isLoading: false,
  })),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");

  return {
    ...actual,
    useParams: () => ({ dagId: "test_dag" }),
  };
});

vi.mock("openapi/queries", () => ({
  useGridServiceGetGridRuns,
}));

vi.mock("src/utils", () => ({
  isStatePending: vi.fn(() => false),
  useAutoRefresh: vi.fn(() => false),
}));

describe("useGridRuns", () => {
  it("forwards the Dag runs tab filter set to the grid endpoint", () => {
    renderHook(() =>
      useGridRuns({
        bundleVersion: "bundle-v2",
        confContains: "partner_id",
        consumingAssetPattern: "sales",
        dagRunState: "success",
        dagVersion: 3,
        durationGte: 10,
        durationLte: 20,
        endDateGte: "2025-01-01T00:00:00Z",
        endDateLte: "2025-01-31T23:59:59Z",
        limit: 25,
        logicalDateGte: "2025-01-01T00:00:00Z",
        logicalDateLte: "2025-01-31T23:59:59Z",
        offset: 5,
        runAfterGte: "2025-02-01T00:00:00Z",
        runAfterLte: "2025-02-28T23:59:59Z",
        runType: "manual",
        startDateGte: "2025-01-01T00:00:00Z",
        startDateLte: "2025-01-31T23:59:59Z",
        triggeringUser: "admin",
      }),
    );

    expect(useGridServiceGetGridRuns).toHaveBeenCalledWith(
      {
        bundleVersion: "bundle-v2",
        confContains: "partner_id",
        consumingAssetPattern: "sales",
        dagId: "test_dag",
        dagVersion: [3],
        durationGte: 10,
        durationLte: 20,
        endDateGte: "2025-01-01T00:00:00Z",
        endDateLte: "2025-01-31T23:59:59Z",
        limit: 25,
        logicalDateGte: "2025-01-01T00:00:00Z",
        logicalDateLte: "2025-01-31T23:59:59Z",
        offset: 5,
        orderBy: ["-run_after"],
        runAfterGte: "2025-02-01T00:00:00Z",
        runAfterLte: "2025-02-28T23:59:59Z",
        runType: ["manual"],
        startDateGte: "2025-01-01T00:00:00Z",
        startDateLte: "2025-01-31T23:59:59Z",
        state: ["success"],
        triggeringUser: "admin",
      },
      undefined,
      expect.objectContaining({
        placeholderData: expect.any(Function),
        refetchInterval: expect.any(Function),
      }),
    );
  });
});
