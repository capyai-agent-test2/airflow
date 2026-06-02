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
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ReactAppResponse } from "openapi/requests/types.gen";

import { loadPlugin } from "./loadReactPlugin";

const makeReactApp = (name: string, bundleUrl: string): ReactAppResponse => ({
  bundle_url: bundleUrl,
  name,
});

const makeBundleUrl = (source: string): string => `data:text/javascript;base64,${btoa(source)}`;

const pluginA = () => undefined;

describe("loadPlugin", () => {
  afterEach(() => {
    delete (globalThis as Record<string, unknown>).AirflowPlugin;
    delete (globalThis as Record<string, unknown>).PluginA;
    delete (globalThis as Record<string, unknown>).PluginB;
    vi.restoreAllMocks();
  });

  it("does not reuse the previous shared AirflowPlugin for a malformed bundle", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    (globalThis as Record<string, unknown>).AirflowPlugin = pluginA;

    await loadPlugin(makeReactApp("PluginB", makeBundleUrl("export {};")));

    expect((globalThis as Record<string, unknown>).PluginB).toBeUndefined();
    expect((globalThis as Record<string, unknown>).AirflowPlugin).toBeUndefined();
  });

  it("clears the shared AirflowPlugin after loading a valid bundle", async () => {
    const { default: pluginComponent } = await loadPlugin(
      makeReactApp("PluginA", makeBundleUrl("globalThis.AirflowPlugin = function PluginA() {}; export {};")),
    );

    expect(pluginComponent).toBe((globalThis as Record<string, unknown>).PluginA);
    expect((globalThis as Record<string, unknown>).AirflowPlugin).toBeUndefined();
  });
});
