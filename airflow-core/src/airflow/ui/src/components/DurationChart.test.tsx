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
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { TaskInstanceResponse } from "openapi/requests/types.gen";
import { Wrapper } from "src/utils/Wrapper";

import { DurationChart } from "./DurationChart";

const barMock = vi.hoisted(() => vi.fn(() => null));

vi.mock("react-chartjs-2", () => ({
  Bar: barMock,
}));

type BarProps = {
  readonly options: {
    readonly plugins: {
      readonly annotation: {
        readonly annotations: {
          readonly medianAnnotation: {
            readonly borderDash: Array<number>;
            readonly label: {
              readonly content: string;
              readonly display: boolean;
            };
            readonly value: number;
          };
        };
      };
      readonly legend: {
        readonly display: boolean;
      };
    };
    readonly scales: {
      readonly y: {
        readonly ticks: {
          readonly callback: (value: number | string) => string;
        };
      };
    };
  };
};

const buildTaskInstance = (durationSeconds: number): TaskInstanceResponse =>
  ({
    dag_id: "dag",
    dag_run_id: `run-${durationSeconds}`,
    end_date: new Date(Date.UTC(2025, 0, 1, 0, 0, durationSeconds)).toISOString(),
    map_index: -1,
    queued_when: null,
    run_after: `2025-01-01T00:00:00Z`,
    start_date: "2025-01-01T00:00:00Z",
    state: "success",
    task_id: "task",
  }) as TaskInstanceResponse;

describe("DurationChart", () => {
  it("shows a legend and a median duration reference line", () => {
    render(
      <DurationChart
        entries={[buildTaskInstance(60), buildTaskInstance(180), buildTaskInstance(360)]}
        kind="Task Instance"
      />,
      { wrapper: Wrapper },
    );

    const bar = barMock as unknown as { mock: { calls: Array<[BarProps]> } };
    const props = bar.mock.calls[0]?.[0];

    expect(props?.options.plugins.legend.display).toBe(true);
    expect(props?.options.plugins.annotation.annotations.medianAnnotation).toMatchObject({
      borderDash: [6, 6],
      label: { content: "00:03:00", display: true },
      value: 180,
    });
    expect(props?.options.scales.y.ticks.callback(180)).toBe("3m");
  });
});
