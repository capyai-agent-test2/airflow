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
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { AppWrapper } from "src/utils/AppWrapper";

describe("Dag Filters", () => {
  it("Filter by selected last run state", async () => {
    render(<AppWrapper initialEntries={["/dags"]} />);

    await waitFor(() => expect(screen.getByText("states.success")).toBeInTheDocument());
    await waitFor(() => screen.getByText("states.success").click());
    await waitFor(() => expect(screen.getByText("tutorial_taskflow_api_success")).toBeInTheDocument());

    await waitFor(() => expect(screen.getByText("states.failed")).toBeInTheDocument());
    await waitFor(() => screen.getByText("states.failed").click());
    await waitFor(() => expect(screen.getByText("tutorial_taskflow_api_failed")).toBeInTheDocument());
  });

  it("filters dags by owner from query params", async () => {
    render(<AppWrapper initialEntries={["/dags?owners=alice"]} />);

    await waitFor(() => expect(screen.getByText("import_error_dag")).toBeInTheDocument());
    expect(screen.queryByText("tutorial_taskflow_api_success")).not.toBeInTheDocument();
  });

  it("keeps owner filtering distinct from import error filtering", async () => {
    render(<AppWrapper initialEntries={["/dags?owners=airflow"]} />);

    await waitFor(() => expect(screen.getByText("tutorial_taskflow_api_success")).toBeInTheDocument());
    expect(screen.getByText("tutorial_taskflow_api_failed")).toBeInTheDocument();
    expect(screen.queryByText("import_error_dag")).not.toBeInTheDocument();
  });

  it("filters dags with import errors from query params", async () => {
    render(<AppWrapper initialEntries={["/dags?has_import_errors=true"]} />);

    await waitFor(() => expect(screen.getByText("import_error_dag")).toBeInTheDocument());
    expect(screen.queryByText("tutorial_taskflow_api_success")).not.toBeInTheDocument();
  });
});
