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
import { render, screen } from "@testing-library/react";
import type * as ReactI18Next from "react-i18next";
import type * as ReactRouterDom from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type * as OpenapiQueries from "openapi/queries";
import { Wrapper } from "src/utils/Wrapper";

import { XCom } from "./XCom";

let mockParams = {
  dagId: "~",
  mapIndex: "-1",
  runId: "~",
  taskId: "~",
};

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
    useParams: () => mockParams,
    useSearchParams: () => [new URLSearchParams(), vi.fn()] as const,
  };
});

vi.mock("openapi/queries", async (importOriginal) => {
  const actual = await importOriginal<typeof OpenapiQueries>();

  return {
    ...actual,
    useXcomServiceGetXcomEntries: vi.fn(),
  };
});

vi.mock("./XComFilters", () => ({
  XComFilters: () => null,
}));

vi.mock("src/components/DataTable", () => ({
  DataTable: ({ columns }: { readonly columns: ReadonlyArray<{ header?: string }> }) => (
    <>
      {columns.map((column) =>
        column.header === undefined || column.header === "" ? null : (
          <div key={column.header}>{column.header}</div>
        ),
      )}
    </>
  ),
}));

const { useXcomServiceGetXcomEntries } = await import("openapi/queries");

beforeEach(() => {
  mockParams = {
    dagId: "~",
    mapIndex: "-1",
    runId: "~",
    taskId: "~",
  };
  vi.mocked(useXcomServiceGetXcomEntries).mockReturnValue({
    data: { total_entries: 0, xcom_entries: [] },
    error: undefined,
    isFetching: false,
    isLoading: false,
  } as ReturnType<typeof useXcomServiceGetXcomEntries>);
});

describe("XCom", () => {
  it("shows context columns on the global XCom page", () => {
    render(<XCom />, { wrapper: Wrapper });

    expect(screen.getByText("xcom.columns.dag")).toBeInTheDocument();
    expect(screen.getByText("common:dagRunId")).toBeInTheDocument();
    expect(screen.getByText("common:dagRun.runAfter")).toBeInTheDocument();
    expect(screen.getByText("common:task_one")).toBeInTheDocument();
    expect(screen.getByText("common:mapIndex")).toBeInTheDocument();
  });

  it("hides redundant context columns on the task instance XCom page", () => {
    mockParams = {
      dagId: "example-dag",
      mapIndex: "3",
      runId: "scheduled__2026-06-07T00:00:00+00:00",
      taskId: "example-task",
    };

    render(<XCom />, { wrapper: Wrapper });

    expect(screen.queryByText("xcom.columns.dag")).not.toBeInTheDocument();
    expect(screen.queryByText("common:dagRunId")).not.toBeInTheDocument();
    expect(screen.queryByText("common:dagRun.runAfter")).not.toBeInTheDocument();
    expect(screen.queryByText("common:task_one")).not.toBeInTheDocument();
    expect(screen.queryByText("common:mapIndex")).not.toBeInTheDocument();
    expect(screen.getByText("xcom.columns.key")).toBeInTheDocument();
    expect(screen.getByText("dashboard:timestamp")).toBeInTheDocument();
    expect(screen.getByText("xcom.columns.value")).toBeInTheDocument();
  });
});
