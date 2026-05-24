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
import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { BaseWrapper } from "src/utils/Wrapper";

import { TriggerDagRouteModal } from "./TriggerDagRouteModal";

vi.mock("./TriggerDAGModal", () => ({
  default: ({
    onClose,
    prefillConfig,
  }: {
    readonly onClose: () => void;
    readonly prefillConfig: unknown;
  }) => (
    <div>
      <button onClick={onClose} type="button">
        Close
      </button>
      <pre data-testid="prefill-config">{JSON.stringify(prefillConfig)}</pre>
    </div>
  ),
}));

const renderComponent = (initialEntry: string) => {
  const router = createMemoryRouter(
    [
      {
        element: <TriggerDagRouteModal dagDisplayName="Example Dag" dagId="example_dag" isPaused={false} />,
        path: "/dags/:dagId/*",
      },
    ],
    { initialEntries: [initialEntry] },
  );

  return render(
    <BaseWrapper>
      <RouterProvider router={router} />
    </BaseWrapper>,
  );
};

describe("TriggerDagRouteModal", () => {
  it("opens the trigger modal from the route and maps query params to prefill config", () => {
    renderComponent(
      "/dags/example_dag/trigger?message=hello&logical_date=2026-01-01T00:00&dag_run_id=manual__123&note=queued",
    );

    expect(screen.getByTestId("prefill-config")).toHaveTextContent(
      '{"logicalDate":"2026-01-01T00:00","dagRunId":"manual__123","note":"queued","conf":{"message":"hello"}}',
    );
  });

  it("defaults interval mode to manual when interval bounds are prefilled from the URL", () => {
    renderComponent("/dags/example_dag/trigger?data_interval_start=2026-01-01T00:00&data_interval_end=2026-01-02T00:00");

    expect(screen.getByTestId("prefill-config")).toHaveTextContent(
      '{"dataIntervalStart":"2026-01-01T00:00","dataIntervalEnd":"2026-01-02T00:00","dataIntervalMode":"manual"}',
    );
  });

  it("closes the route-backed modal by navigating to the parent Dag page", () => {
    renderComponent("/dags/example_dag/trigger?message=hello");

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.queryByTestId("prefill-config")).not.toBeInTheDocument();
  });
});
