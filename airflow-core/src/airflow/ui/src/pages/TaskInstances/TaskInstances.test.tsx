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
import type { CellContext, ColumnDef } from "@tanstack/react-table";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import type * as ReactI18Next from "react-i18next";
import type * as ReactRouterDom from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type * as OpenapiQueries from "openapi/queries";
import type { TaskInstanceResponse } from "openapi/requests/types.gen";
import type * as SrcUtils from "src/utils";
import { Wrapper } from "src/utils/Wrapper";

import { TaskInstances } from "./TaskInstances";

let capturedColumns: Array<ColumnDef<TaskInstanceResponse>> = [];

vi.mock("react-i18next", async (importOriginal) => {
  const actual = await importOriginal<typeof ReactI18Next>();

  return {
    ...actual,
    useTranslation: () => ({
      // eslint-disable-next-line id-length
      t: (key: string) => key,
    }),
  };
});

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof ReactRouterDom>();

  return {
    ...actual,
    useParams: () => ({ dagId: "example_dag", runId: "example_run", taskId: "mapped_task" }),
    useSearchParams: () => [new URLSearchParams(), vi.fn()] as const,
  };
});

vi.mock("openapi/queries", async (importOriginal) => {
  const actual = await importOriginal<typeof OpenapiQueries>();

  return {
    ...actual,
    useTaskInstanceServiceGetTaskInstances: vi.fn(),
  };
});

vi.mock("src/components/DataTable", () => ({
  DataTable: ({ columns }: { columns: Array<ColumnDef<TaskInstanceResponse>> }) => {
    capturedColumns = columns;

    return null;
  },
}));

vi.mock("src/components/DataTable/useRowSelection", () => ({
  useRowSelection: () => ({
    allRowsSelected: false,
    clearSelections: vi.fn(),
    deselectKeys: vi.fn(),
    handleRowSelect: vi.fn(),
    handleSelectAll: vi.fn(),
    selectedRows: new Set<string>(),
  }),
}));

vi.mock("src/components/DataTable/useTableUrlState", () => ({
  useTableURLState: () => ({
    setTableURLState: vi.fn(),
    tableURLState: {
      columnVisibility: {},
      cursor: undefined,
      pagination: { pageIndex: 0, pageSize: 25 },
      sorting: [],
    },
  }),
}));

vi.mock("src/hooks/useAdvancedSearch", () => ({
  useAdvancedSearchArg: () => ({}),
}));

vi.mock("src/utils", async (importOriginal) => {
  const actual = await importOriginal<typeof SrcUtils>();

  return {
    ...actual,
    useAutoRefresh: () => false,
  };
});

vi.mock("./TaskInstancesFilter", () => ({
  TaskInstancesFilter: () => null,
}));

vi.mock("./BulkClearTaskInstancesButton", () => ({
  default: () => null,
}));

vi.mock("./BulkDeleteTaskInstancesButton", () => ({
  default: () => null,
}));

vi.mock("./BulkMarkTaskInstancesAsButton", () => ({
  default: () => null,
}));

const { useTaskInstanceServiceGetTaskInstances } = await import("openapi/queries");

const taskInstance = {
  dag_display_name: "Example Dag",
  dag_id: "example_dag",
  dag_run_id: "example_run",
  duration: null,
  end_date: null,
  executor: null,
  hostname: null,
  id: "1",
  map_index: 2,
  note: null,
  operator_name: "PythonOperator",
  pool: "default_pool",
  priority_weight: 1,
  queue: "default",
  rendered_map_index: "2",
  run_after: "2026-06-07T12:00:00+00:00",
  start_date: null,
  state: "queued",
  task_display_name: "mapped_task",
  task_id: "mapped_task",
  try_number: 1,
} as unknown as TaskInstanceResponse;

const findColumn = (accessorKey: string) => {
  const column = capturedColumns.find(
    (candidate) => "accessorKey" in candidate && candidate.accessorKey === accessorKey,
  );

  if (column?.cell === undefined) {
    throw new Error(`Column '${accessorKey}' not found`);
  }

  return column;
};

const getCellRenderer = (accessorKey: string) => {
  const column = findColumn(accessorKey);

  if (typeof column.cell !== "function") {
    throw new TypeError(`Column '${accessorKey}' does not use a function cell renderer`);
  }

  return column.cell as (context: CellContext<TaskInstanceResponse, unknown>) => ReactNode;
};

beforeEach(() => {
  capturedColumns = [];
  vi.mocked(useTaskInstanceServiceGetTaskInstances).mockReturnValue({
    data: {
      next_cursor: null,
      previous_cursor: null,
      task_instances: [taskInstance],
      total_entries: 1,
    },
    error: null,
    isLoading: false,
  } as ReturnType<typeof useTaskInstanceServiceGetTaskInstances>);
});

describe("TaskInstances", () => {
  it("links mapped rows from the map index cell when start date is absent", () => {
    render(<TaskInstances />, { wrapper: Wrapper });

    const renderMapIndexCell = getCellRenderer("rendered_map_index");
    const mapIndexCell = renderMapIndexCell({ row: { original: taskInstance } } as CellContext<
      TaskInstanceResponse,
      unknown
    >);

    render(mapIndexCell, { wrapper: Wrapper });

    expect(screen.getByRole("link", { name: "2" })).toHaveAttribute(
      "href",
      "/dags/example_dag/runs/example_run/tasks/mapped_task/mapped/2",
    );
  });
});
