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
import type { FC } from "react";

import type { ReactAppResponse } from "openapi/requests/types.gen";

import { ErrorPage } from "./Error";

export type PluginProps = {
  dagId?: string;
  mapIndex?: string;
  runId?: string;
  taskId?: string;
};

export type PluginComponentType = FC<PluginProps>;

export const loadPlugin = (reactApp: ReactAppResponse): Promise<{ default: PluginComponentType }> => {
  const globalObject = globalThis as Record<string, unknown>;

  globalObject.AirflowPlugin = undefined;

  return (
    // We are assuming the plugin manager is trusted and the bundle_url is safe
    import(/* @vite-ignore */ new URL(reactApp.bundle_url, document.baseURI).href)
      .then(() => {
        // Store components in globalThis[reactApp.name] to avoid conflicts with the shared globalThis.AirflowPlugin
        // global variable.
        let pluginComponent = globalObject[reactApp.name] as PluginComponentType | undefined;

        if (pluginComponent === undefined) {
          pluginComponent = globalObject.AirflowPlugin as PluginComponentType;

          globalObject[reactApp.name] = pluginComponent;
        }

        globalObject.AirflowPlugin = undefined;

        if (typeof pluginComponent !== "function") {
          throw new TypeError(`Expected function, got ${typeof pluginComponent} for plugin ${reactApp.name}`);
        }

        return { default: pluginComponent };
      })
      .catch((error: unknown) => {
        globalObject.AirflowPlugin = undefined;

        // eslint-disable-next-line no-console
        console.error("Component failed to load:", error);

        return { default: ErrorPage };
      })
  );
};
