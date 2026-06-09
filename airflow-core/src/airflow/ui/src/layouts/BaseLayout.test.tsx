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
import { render, waitFor } from "@testing-library/react";
import type { Location } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BaseLayout } from "src/layouts/BaseLayout";
import { Wrapper } from "src/utils/Wrapper";

const useConfigMock = vi.fn<(key: string) => unknown>();
const useLocationMock = vi.fn<() => Pick<Location, "pathname">>();

vi.mock("src/queries/useConfig", () => ({
  useConfig: (key: string) => useConfigMock(key),
}));

vi.mock("openapi/queries", () => ({
  usePluginServiceGetPlugins: () => ({ data: { plugins: [] } }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    i18n: {
      dir: () => "ltr",
      language: "en",
      off: vi.fn(),
      on: vi.fn(),
    },
  }),
}));

vi.mock("src/layouts/Nav", () => ({
  Nav: () => null,
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");

  return {
    ...actual,
    useLocation: () => useLocationMock(),
  };
});

describe("BaseLayout", () => {
  beforeEach(() => {
    useConfigMock.mockReset();
    useLocationMock.mockReturnValue({ pathname: "/" });
  });

  it("uses the configured instance name as the default browser title", async () => {
    useConfigMock.mockImplementation((key: string) => (key === "instance_name" ? "My Airflow" : undefined));

    render(<BaseLayout />, { wrapper: Wrapper });

    await waitFor(() => expect(document.title).toBe("My Airflow"));
  });

  it("uses the default browser title on non-Dag pages", async () => {
    useConfigMock.mockReturnValue(undefined);

    render(<BaseLayout />, { wrapper: Wrapper });

    await waitFor(() => expect(document.title).toBe("Airflow"));
  });

  it("does not override Dag-specific page titles", async () => {
    useConfigMock.mockImplementation((key: string) => (key === "instance_name" ? "My Airflow" : undefined));
    useLocationMock.mockReturnValue({ pathname: "/dags/example" });
    document.title = "Example Dag - My Airflow";

    render(<BaseLayout />, { wrapper: Wrapper });

    await waitFor(() => expect(document.title).toBe("Example Dag - My Airflow"));
  });
});
