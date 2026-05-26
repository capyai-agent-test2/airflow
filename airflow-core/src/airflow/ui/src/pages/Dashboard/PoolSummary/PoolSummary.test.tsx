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
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import type { UseQueryResult } from "@tanstack/react-query";
import type * as OpenApiQueriesModule from "openapi/queries";
import type { PoolResponse } from "openapi/requests/types.gen";
import type { ComponentProps, JSX } from "react";
import type * as UtilsModule from "src/utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BaseWrapper } from "src/utils/Wrapper";

import { PoolSummary } from "./PoolSummary";

type AuthMenusResult = {
  data: {
    authorized_menu_items: Array<string>;
  };
};
type PoolsQueryResult = Partial<UseQueryResult<{ pools: Array<PoolResponse> }>>;
type PoolBarProps = {
  pool: {
    deferred_slots: number;
    open_slots: number;
  };
  totalSlots: number;
};

const mockUseAuthLinksServiceGetAuthMenus = vi.fn<() => AuthMenusResult>();
const mockUsePoolServiceGetPools = vi.fn<() => PoolsQueryResult>();
const mockPoolBar = vi.fn<(props: PoolBarProps) => JSX.Element>(() => <div data-testid="pool-bar" />);
const translate = (key: string) => key;
const buildQueryResult = (pools: Array<PoolResponse>): PoolsQueryResult => ({
  data: { pools },
  error: undefined,
  isLoading: false,
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    // eslint-disable-next-line id-length
    t: translate,
  }),
}));

vi.mock("openapi/queries", async (importOriginal) => {
  const actual: typeof OpenApiQueriesModule = await importOriginal();

  return {
    ...actual,
    useAuthLinksServiceGetAuthMenus: () => mockUseAuthLinksServiceGetAuthMenus(),
  };
});

vi.mock("openapi/queries/queries", () => ({
  usePoolServiceGetPools: () => mockUsePoolServiceGetPools(),
}));

vi.mock("src/components/PoolBar", () => ({
  PoolBar: (props: unknown) => {
    mockPoolBar(props);

    return <div data-testid="pool-bar" />;
  },
  UNLIMITED_SLOTS: -1,
}));

vi.mock("src/components/ui", () => ({
  RouterLink: ({ children, ...props }: ComponentProps<"a">) => <a {...props}>{children}</a>,
}));

vi.mock("src/utils", async (importOriginal) => {
  const actual: typeof UtilsModule = await importOriginal();

  return {
    ...actual,
    useAutoRefresh: () => false,
  };
});

describe("PoolSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("omits deferred slots from the dashboard summary when the pool does not consume them", () => {
    const pools = [
      {
        deferred_slots: 1,
        include_deferred: false,
        name: "default_pool",
        occupied_slots: 0,
        open_slots: 128,
        queued_slots: 0,
        running_slots: 0,
        scheduled_slots: 0,
        slots: 128,
        team_name: null,
      },
    ] satisfies Array<PoolResponse>;

    mockUseAuthLinksServiceGetAuthMenus.mockReturnValue({
      data: { authorized_menu_items: ["Pools"] },
    });
    mockUsePoolServiceGetPools.mockReturnValue(buildQueryResult(pools));

    render(<PoolSummary />, { wrapper: BaseWrapper });

    expect(screen.getByTestId("pool-bar")).toBeInTheDocument();
    const [firstCall] = mockPoolBar.mock.calls;

    expect(firstCall?.[0].pool.deferred_slots).toBe(0);
    expect(firstCall?.[0].pool.open_slots).toBe(128);
    expect(firstCall?.[0].totalSlots).toBe(128);
  });

  it("keeps deferred slots in the dashboard summary when the pool consumes them", () => {
    const pools = [
      {
        deferred_slots: 1,
        include_deferred: true,
        name: "default_pool",
        occupied_slots: 1,
        open_slots: 127,
        queued_slots: 0,
        running_slots: 0,
        scheduled_slots: 0,
        slots: 128,
        team_name: null,
      },
    ] satisfies Array<PoolResponse>;

    mockUseAuthLinksServiceGetAuthMenus.mockReturnValue({
      data: { authorized_menu_items: ["Pools"] },
    });
    mockUsePoolServiceGetPools.mockReturnValue(buildQueryResult(pools));

    render(<PoolSummary />, { wrapper: BaseWrapper });

    const [firstCall] = mockPoolBar.mock.calls;

    expect(firstCall?.[0].pool.deferred_slots).toBe(1);
    expect(firstCall?.[0].pool.open_slots).toBe(127);
    expect(firstCall?.[0].totalSlots).toBe(128);
  });
});
