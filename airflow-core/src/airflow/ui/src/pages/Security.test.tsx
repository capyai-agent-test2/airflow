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
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { useAuthLinksServiceGetAuthMenus } from "openapi/queries";
import { Security } from "src/pages/Security";
import { BaseWrapper } from "src/utils/Wrapper";

vi.mock("openapi/queries", () => ({
  useAuthLinksServiceGetAuthMenus: vi.fn(),
}));

const mockedUseAuthLinksServiceGetAuthMenus = vi.mocked(useAuthLinksServiceGetAuthMenus);

const LocationDisplay = () => {
  const location = useLocation();

  return <div data-testid="location">{`${location.pathname}${location.search}${location.hash}`}</div>;
};

describe("Security", () => {
  it("builds the iframe source from a deep link detail path", () => {
    mockedUseAuthLinksServiceGetAuthMenus.mockReturnValue({
      data: {
        authorized_menu_items: [],
        extra_menu_items: [{ href: "/auth/users/list/", text: "Users" }],
      },
      isLoading: false,
    } as ReturnType<typeof useAuthLinksServiceGetAuthMenus>);

    render(
      <BaseWrapper>
        <MemoryRouter initialEntries={["/security/users/edit/2"]}>
          <Routes>
            <Route element={<Security />} path="/security/:page/*" />
          </Routes>
        </MemoryRouter>
      </BaseWrapper>,
    );

    const iframe = screen.getByTitle("Users");

    expect(iframe).toHaveAttribute("src", "/auth/users/edit/2");
  });

  it("syncs the parent route with the iframe location after navigation", () => {
    mockedUseAuthLinksServiceGetAuthMenus.mockReturnValue({
      data: {
        authorized_menu_items: [],
        extra_menu_items: [{ href: "/auth/users/list/", text: "Users" }],
      },
      isLoading: false,
    } as ReturnType<typeof useAuthLinksServiceGetAuthMenus>);

    render(
      <BaseWrapper>
        <MemoryRouter initialEntries={["/security/users"]}>
          <Routes>
            <Route
              element={
                <>
                  <Security />
                  <LocationDisplay />
                </>
              }
              path="/security/:page/*"
            />
          </Routes>
        </MemoryRouter>
      </BaseWrapper>,
    );

    const iframe = screen.getByTitle("Users");

    Object.defineProperty(iframe, "contentWindow", {
      configurable: true,
      value: {
        location: {
          hash: "",
          pathname: "/auth/users/edit/2",
          search: "",
        },
      },
    });

    fireEvent.load(iframe);

    expect(screen.getByTestId("location")).toHaveTextContent("/security/users/edit/2");
  });
});
