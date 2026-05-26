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
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { useDagServiceGetDag, useDagWarningServiceListDagWarnings } from "openapi/queries";
import { useGridRuns } from "src/queries/useGridRuns.ts";
import { BaseWrapper } from "src/utils/Wrapper";

import { DetailsLayout } from "./DetailsLayout";

const mockNavigate = vi.fn();
const translateMock = (translationKey: string) => translationKey;

let mockParams: Record<string, string> = { dagId: "example_dag" };
let mockSearchParams = new URLSearchParams("view=graph");

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");

  return {
    ...actual,
    Outlet: () => null,
    useNavigate: () => mockNavigate,
    useParams: () => mockParams,
    useSearchParams: () => [mockSearchParams, vi.fn()],
  };
});

vi.mock("usehooks-ts", () => ({
  useLocalStorage: vi.fn(() => ["graph", vi.fn()]),
}));

vi.mock("react-i18next", () => ({
  useTranslation: vi.fn(() => ({
    i18n: { dir: () => "ltr" },
    // eslint-disable-next-line id-length
    t: translateMock,
  })),
}));

vi.mock("@xyflow/react", () => ({
  useReactFlow: vi.fn(() => ({ fitView: vi.fn(), getZoom: vi.fn(() => 1) })),
}));

vi.mock("openapi/queries", () => ({
  useDagRunServiceGetDagRun: vi.fn(() => ({ data: undefined })),
  useDagServiceGetDag: vi.fn(() => ({ data: undefined })),
  useDagWarningServiceListDagWarnings: vi.fn(() => ({ data: { dag_warnings: [], total_entries: 0 } })),
}));

vi.mock("src/queries/useGridRuns.ts", () => ({
  useGridRuns: vi.fn(() => ({ data: [] })),
}));

vi.mock("src/context/groups", () => ({
  GroupsProvider: ({ children }: { children: ReactNode }) => children,
}));

vi.mock("src/context/hover", () => ({
  HoverProvider: ({ children }: { children: ReactNode }) => children,
  useHover: vi.fn(() => ({ setHoveredTaskId: vi.fn() })),
}));

vi.mock("./DagBreadcrumb", () => ({ DagBreadcrumb: () => null }));
vi.mock("./Gantt/Gantt", () => ({ Gantt: () => null }));
vi.mock("./Graph", () => ({ Graph: () => null }));
vi.mock("./Grid", () => ({ Grid: () => null }));
vi.mock("./NavTabs", () => ({ NavTabs: () => null }));
vi.mock("./PanelButtons", () => ({ PanelButtons: () => null }));
vi.mock("src/components/Banner/BackfillBanner", () => ({ default: () => null }));
vi.mock("src/components/DAGWarningsModal", () => ({ DAGWarningsModal: () => null }));
vi.mock("src/components/SearchDags", () => ({ SearchDagsButton: () => null }));
vi.mock("src/components/TriggerDag/TriggerDAGButton", () => ({ TriggerDAGButton: () => null }));
vi.mock("src/components/ui", () => ({
  IconButton: () => null,
  ProgressBar: () => null,
  Toaster: () => null,
}));

describe("DetailsLayout", () => {
  it("navigates to the latest Dag run when graph view opens without a selected run", () => {
    mockParams = { dagId: "example_dag" };
    mockSearchParams = new URLSearchParams("view=graph&limit=10");
    vi.mocked(useDagServiceGetDag).mockReturnValue({ data: undefined } as ReturnType<typeof useDagServiceGetDag>);
    vi.mocked(useDagWarningServiceListDagWarnings).mockReturnValue({
      data: { dag_warnings: [], total_entries: 0 },
    } as ReturnType<typeof useDagWarningServiceListDagWarnings>);
    vi.mocked(useGridRuns).mockReturnValue({
      data: [{ run_after: "2025-01-01T00:00:00Z", run_id: "latest_run", state: "success" }],
    } as ReturnType<typeof useGridRuns>);

    render(
      <DetailsLayout tabs={[]}>
        <div />
      </DetailsLayout>,
      { wrapper: BaseWrapper },
    );

    expect(mockNavigate).toHaveBeenCalledWith(
      {
        pathname: "/dags/example_dag/runs/latest_run",
        search: "view=graph&limit=10",
      },
      { replace: true },
    );
  });

  it("does not navigate when a Dag run is already selected", () => {
    mockNavigate.mockClear();
    mockParams = { dagId: "example_dag", runId: "existing_run" };
    mockSearchParams = new URLSearchParams("view=graph");
    vi.mocked(useGridRuns).mockReturnValue({
      data: [{ run_after: "2025-01-01T00:00:00Z", run_id: "latest_run", state: "success" }],
    } as ReturnType<typeof useGridRuns>);

    render(
      <DetailsLayout tabs={[]}>
        <div />
      </DetailsLayout>,
      { wrapper: BaseWrapper },
    );

    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
