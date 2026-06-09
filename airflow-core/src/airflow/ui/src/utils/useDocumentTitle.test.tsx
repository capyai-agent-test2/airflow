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
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Wrapper } from "src/utils/Wrapper";
import { useDocumentTitle } from "src/utils/useDocumentTitle";

const useConfigMock = vi.fn<(key: string) => unknown>();

vi.mock("src/queries/useConfig", () => ({
  useConfig: (key: string) => useConfigMock(key),
}));

const TestComponent = ({ pageTitle }: { readonly pageTitle?: string | null }) => {
  useDocumentTitle(pageTitle);

  return null;
};

const DisabledDefaultTitleComponent = () => {
  useDocumentTitle(undefined, false);

  return null;
};

describe("useDocumentTitle", () => {
  beforeEach(() => {
    useConfigMock.mockReset();
  });

  it("uses the configured instance name when no page title is provided", () => {
    useConfigMock.mockReturnValue("My Airflow");

    const previousTitle = document.title;
    const { unmount } = render(<TestComponent />, { wrapper: Wrapper });

    expect(document.title).toBe("My Airflow");

    unmount();

    expect(document.title).toBe(previousTitle);
  });

  it("formats Dag page titles with the configured instance name", () => {
    useConfigMock.mockReturnValue("My Airflow");

    render(<TestComponent pageTitle="Example Dag" />, { wrapper: Wrapper });

    expect(document.title).toBe("Example Dag - My Airflow");
  });

  it("falls back to Airflow when the configured instance name is empty", () => {
    useConfigMock.mockReturnValue("");

    render(<TestComponent />, { wrapper: Wrapper });

    expect(document.title).toBe("Airflow");
  });

  it("does not change the title when default title handling is disabled", () => {
    useConfigMock.mockReturnValue("My Airflow");
    document.title = "Example Dag - My Airflow";

    render(<DisabledDefaultTitleComponent />, { wrapper: Wrapper });

    expect(document.title).toBe("Example Dag - My Airflow");
  });

  it("does not restore a stale title when disabled default title handling unmounts", () => {
    useConfigMock.mockReturnValue("My Airflow");
    document.title = "Example Dag - My Airflow";

    const { rerender, unmount } = render(<DisabledDefaultTitleComponent />, { wrapper: Wrapper });

    document.title = "Updated Dag - My Airflow";
    rerender(<DisabledDefaultTitleComponent />);
    unmount();

    expect(document.title).toBe("Updated Dag - My Airflow");
  });
});
