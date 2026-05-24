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
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AssetEventDetails } from "src/components/Assets/AssetEventDetails";
import { Wrapper } from "src/utils/Wrapper";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    i18n: { dir: () => "ltr" },
    // eslint-disable-next-line id-length
    t: (translationKey: string) => translationKey,
  }),
}));

vi.mock("src/components/RenderedJsonField", () => ({
  default: ({ content }: { content: object }) => <pre>{JSON.stringify(content)}</pre>,
}));

describe("AssetEventDetails", () => {
  it("shows related Dag runs and queued consumers for the selected event", () => {
    render(
      <Wrapper>
        <AssetEventDetails
          event={{
            asset_id: 42,
            created_dagruns: [
              {
                dag_id: "consumer_dag",
                data_interval_end: null,
                data_interval_start: null,
                end_date: null,
                logical_date: null,
                partition_key: null,
                run_id: "asset_run",
                start_date: "2025-01-01T00:00:01Z",
                state: "queued",
              },
            ],
            extra: { from_rest_api: true },
            group: "analytics",
            id: 7,
            name: "warehouse",
            partition_key: "daily",
            source_dag_id: null,
            source_map_index: -1,
            source_run_id: null,
            source_task_id: null,
            timestamp: "2025-01-01T00:00:00Z",
            uri: "s3://warehouse",
          }}
          queuedEvents={{
            queued_events: [
              {
                asset_id: 42,
                created_at: "2025-01-01T00:00:02Z",
                dag_display_name: "Consumer Dag",
                dag_id: "consumer_dag",
              },
            ],
            total_entries: 1,
          }}
        />
      </Wrapper>,
    );

    expect(screen.getByTestId("asset-event-details")).toBeInTheDocument();
    expect(screen.getByText("common:assetEvent_one")).toBeInTheDocument();
    expect(screen.getByText("API")).toBeInTheDocument();
    expect(screen.getByText("daily")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "consumer_dag" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Consumer Dag" })).toBeInTheDocument();
  });

  it("filters out queued events older than the selected event", () => {
    render(
      <Wrapper>
        <AssetEventDetails
          event={{
            asset_id: 42,
            created_dagruns: [],
            extra: null,
            group: "analytics",
            id: 8,
            name: "warehouse",
            partition_key: null,
            source_dag_id: "producer_dag",
            source_map_index: -1,
            source_run_id: "producer_run",
            source_task_id: "produce",
            timestamp: "2025-01-01T00:00:10Z",
            uri: "s3://warehouse",
          }}
          queuedEvents={{
            queued_events: [
              {
                asset_id: 42,
                created_at: "2025-01-01T00:00:05Z",
                dag_display_name: "Old Consumer Dag",
                dag_id: "old_consumer_dag",
              },
            ],
            total_entries: 1,
          }}
        />
      </Wrapper>,
    );

    expect(screen.queryByRole("link", { name: "Old Consumer Dag" })).not.toBeInTheDocument();
    expect(screen.queryByText("common:pendingDagRun_other")).not.toBeInTheDocument();
  });

  it("does not show the active badge when there are no pending Dag runs", () => {
    render(
      <Wrapper>
        <AssetEventDetails
          event={{
            asset_id: 42,
            created_dagruns: [
              {
                dag_id: "consumer_dag",
                data_interval_end: null,
                data_interval_start: null,
                end_date: "2025-01-01T00:00:03Z",
                logical_date: null,
                partition_key: null,
                run_id: "finished_asset_run",
                start_date: "2025-01-01T00:00:01Z",
                state: "success",
              },
            ],
            extra: null,
            group: "analytics",
            id: 9,
            name: "warehouse",
            partition_key: null,
            source_dag_id: "producer_dag",
            source_map_index: -1,
            source_run_id: "producer_run",
            source_task_id: "produce",
            timestamp: "2025-01-01T00:00:00Z",
            uri: "s3://warehouse",
          }}
          queuedEvents={{ queued_events: [], total_entries: 0 }}
        />
      </Wrapper>,
    );

    expect(screen.queryByText("common:states.running")).not.toBeInTheDocument();
  });
});
