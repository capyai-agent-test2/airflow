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

import { useTogglePause } from "./useTogglePause";

const invalidateQueries = vi.fn().mockResolvedValue(undefined);
const capturedOptions = vi.hoisted(() => ({
  current: undefined as { onSuccess?: () => Promise<void> | void } | undefined,
}));

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({
    invalidateQueries,
  }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    // eslint-disable-next-line id-length
    t: (translationKey: string) => translationKey,
  }),
}));

vi.mock("openapi/queries", () => {
  const optionsByHook = (options: { onSuccess?: () => Promise<void> | void }) => {
    capturedOptions.current = options;

    return { mutate: vi.fn() };
  };

  return {
    UseDagRunServiceGetDagRunsKeyFn: ({ dagId }: { dagId: string }, queryKey?: Array<unknown>) => [
      "DagRunServiceGetDagRuns",
      ...(queryKey ?? [{ dagId }]),
    ],
    UseDagServiceGetDagDetailsKeyFn: ({ dagId }: { dagId: string }, queryKey?: Array<unknown>) => [
      "DagServiceGetDagDetails",
      ...(queryKey ?? [{ dagId }]),
    ],
    UseDagServiceGetDagKeyFn: ({ dagId }: { dagId: string }, queryKey?: Array<unknown>) => [
      "DagServiceGetDag",
      ...(queryKey ?? [{ dagId }]),
    ],
    useDagServiceGetDagsUiKey: "DagServiceGetDagsUi",
    UseDagServiceGetLatestRunInfoKeyFn: ({ dagId }: { dagId: string }, queryKey?: Array<unknown>) => [
      "DagServiceGetLatestRunInfo",
      ...(queryKey ?? [{ dagId }]),
    ],
    useDagServicePatchDag: vi.fn(optionsByHook),
    UseTaskInstanceServiceGetTaskInstancesKeyFn: (
      { dagId, dagRunId }: { dagId: string; dagRunId: string },
      queryKey?: Array<unknown>,
    ) => ["TaskInstanceServiceGetTaskInstances", ...(queryKey ?? [{ dagId, dagRunId }])],
  };
});

describe("useTogglePause", () => {
  it("invalidates the latest Dag run query after toggling pause", async () => {
    renderHook(() => useTogglePause({ dagId: "example_dag" }));

    await capturedOptions.current?.onSuccess?.();

    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["DagServiceGetLatestRunInfo", { dagId: "example_dag" }],
    });
  });
});
