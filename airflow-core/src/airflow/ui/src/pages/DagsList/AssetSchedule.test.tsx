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
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAssetServiceGetDagAssetQueuedEvents, useAssetServiceNextRunAssets } from "openapi/queries";
import { BaseWrapper } from "src/utils/Wrapper";

import { AssetSchedule } from "./AssetSchedule";

vi.mock("openapi/queries", () => ({
  useAssetServiceGetDagAssetQueuedEvents: vi.fn(),
  useAssetServiceNextRunAssets: vi.fn(),
}));

const mockTranslate = vi.fn((key: string, values?: { count?: number; total?: number }) =>
  key === "assetSchedule" ? `${String(values?.count)} of ${String(values?.total)} assets updated` : key,
);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    // eslint-disable-next-line id-length
    t: mockTranslate,
  }),
}));

const mockUseAssetServiceNextRunAssets = vi.mocked(useAssetServiceNextRunAssets);
const mockUseAssetServiceGetDagAssetQueuedEvents = vi.mocked(useAssetServiceGetDagAssetQueuedEvents);

describe("AssetSchedule", () => {
  beforeEach(() => {
    mockUseAssetServiceGetDagAssetQueuedEvents.mockReturnValue({
      data: { queued_events: [], total_entries: 0 },
      isLoading: false,
    } as ReturnType<typeof useAssetServiceGetDagAssetQueuedEvents>);
  });

  it("counts next run asset updates when queued events are not loaded yet", () => {
    mockUseAssetServiceNextRunAssets.mockReturnValue({
      data: {
        asset_expression: { all: [{ asset: { id: 1, name: "A", uri: "s3://bucket/A" } }] },
        events: [
          { id: 1, lastUpdate: "2024-01-01T00:00:00Z", name: "A", uri: "s3://bucket/A" },
          { id: 2, lastUpdate: "2024-01-01T00:00:00Z", name: "B", uri: "s3://bucket/B" },
          { id: 3, lastUpdate: null, name: "C", uri: "s3://bucket/C" },
        ],
      },
      isLoading: false,
    } as ReturnType<typeof useAssetServiceNextRunAssets>);

    render(
      <AssetSchedule
        assetExpression={undefined}
        dagId="consumer"
        timetablePartitioned={false}
        timetableSummary="Asset"
      />,
      { wrapper: BaseWrapper },
    );

    expect(screen.getByRole("button", { name: /2 of 3 assets updated/u })).toBeInTheDocument();
  });
});
