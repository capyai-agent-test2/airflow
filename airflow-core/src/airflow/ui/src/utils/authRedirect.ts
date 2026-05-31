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
type RedirectLocation = Pick<Location, "hash" | "pathname" | "replace" | "search">;

const getLoginPath = (): string => {
  const baseHref = document.querySelector("head > base")?.getAttribute("href") ?? "";
  const baseUrl = new URL(baseHref, globalThis.location.origin);

  return new URL("api/v2/auth/login", baseUrl).pathname;
};

export const redirectToLogin = (location: RedirectLocation = globalThis.location): Promise<never> => {
  const params = new URLSearchParams();

  params.set("next", `${location.pathname}${location.search}${location.hash}`);
  location.replace(`${getLoginPath()}?${params.toString()}`);

  return new Promise<never>(() => {
    // Keep the failed request pending while the browser navigates to the auth manager.
  });
};
