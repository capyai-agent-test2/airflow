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
import type * as OpenapiQueries from "openapi/queries";
import type { ReactNode } from "react";
import type * as XYFlowReact from "@xyflow/react";
import type * as ReactI18Next from "react-i18next";
import type * as ReactRouterDom from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Wrapper } from "src/utils/Wrapper";

import { AssetLayout } from "./AssetLayout";

let mockSearchParams = new URLSearchParams();

vi.mock("react-i18next", async (importOriginal) => {
  const actual = await importOriginal<typeof ReactI18Next>();

  return {
    ...actual,
    useTranslation: () => ({
      i18n: { dir: () => "ltr" },
      // eslint-disable-next-line id-length
      t: (key: string) => key,
    }),
  };
});

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof ReactRouterDom>();

  return {
    ...actual,
    useParams: () => ({ assetId: "7" }),
    useSearchParams: () => [mockSearchParams, vi.fn()] as const,
  };
});

vi.mock("openapi/queries", async (importOriginal) => {
  const actual = await importOriginal<typeof OpenapiQueries>();

  return {
    ...actual,
    useAssetServiceGetAsset: vi.fn(),
    useAssetServiceGetAssetEvents: vi.fn(),
  };
});

vi.mock("@xyflow/react", async (importOriginal) => {
  const actual = await importOriginal<typeof XYFlowReact>();

  return {
    ...actual,
    useReactFlow: () => ({ fitView: vi.fn(), getZoom: vi.fn(() => 1) }),
  };
});

vi.mock("react-resizable-panels", () => ({
  Panel: ({ children }: Readonly<{ children: ReactNode }>) => <div>{children}</div>,
  PanelGroup: ({ children }: Readonly<{ children: ReactNode }>) => <div>{children}</div>,
  PanelResizeHandle: ({ children }: Readonly<{ children: ReactNode }>) => <div>{children}</div>,
}));

vi.mock("src/components/Assets/AssetEvents", () => ({
  AssetEvents: () => null,
}));

vi.mock("src/components/BreadcrumbStats", () => ({
  BreadcrumbStats: () => null,
}));

vi.mock("src/context/groups", () => ({
  GroupsProvider: ({ children }: Readonly<{ children: ReactNode }>) => <div>{children}</div>,
}));

vi.mock("./AssetGraph", () => ({
  AssetGraph: () => null,
}));

vi.mock("./AssetPanelButtons", () => ({
  AssetPanelButtons: () => null,
}));

vi.mock("./CreateAssetEvent", () => ({
  CreateAssetEvent: () => null,
}));

vi.mock("./Header", () => ({
  Header: () => null,
}));

const { useAssetServiceGetAsset, useAssetServiceGetAssetEvents } = await import("openapi/queries");

beforeEach(() => {
  vi.mocked(useAssetServiceGetAsset).mockReturnValue({
    data: { extra: {}, id: 7, name: "asset-7" },
    isLoading: false,
  } as ReturnType<typeof useAssetServiceGetAsset>);
  vi.mocked(useAssetServiceGetAssetEvents).mockReturnValue({
    data: { asset_events: [], total_entries: 0 },
    isLoading: false,
  } as ReturnType<typeof useAssetServiceGetAssetEvents>);
});

describe("AssetLayout", () => {
  it("passes the event type filter from the URL to the asset events query", () => {
    mockSearchParams = new URLSearchParams("event_type=trigger");

    render(<AssetLayout />, { wrapper: Wrapper });

    expect(vi.mocked(useAssetServiceGetAssetEvents)).toHaveBeenCalledWith(
      expect.objectContaining({ eventType: "trigger" }),
      undefined,
      expect.anything(),
    );
  });
});
