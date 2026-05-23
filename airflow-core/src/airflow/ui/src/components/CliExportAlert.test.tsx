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
import { describe, expect, it, vi } from "vitest";

import { Wrapper } from "src/utils/Wrapper";

import { CliExportAlert } from "./CliExportAlert";

const translateKey = (key: string) =>
  (
    ({
      "exportCliOnly.description":
        "Export is available only through the local CLI. Import remains available here in the UI.",
      "exportCliOnly.title": "Export is not available in the UI",
    }) as const
  )[key];

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    // eslint-disable-next-line id-length
    t: translateKey,
  }),
}));

describe("CliExportAlert", () => {
  it("explains that export is only available through the cli", () => {
    render(<CliExportAlert />, { wrapper: Wrapper });

    expect(screen.getByText("Export is not available in the UI")).toBeVisible();
    expect(
      screen.getByText(
        "Export is available only through the local CLI. Import remains available here in the UI.",
      ),
    ).toBeVisible();
  });
});
