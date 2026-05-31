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
import { describe, expect, it, vi } from "vitest";

import { redirectToLogin } from "./authRedirect";

describe("redirectToLogin", () => {
  it("redirects to login and keeps the original request pending", async () => {
    const replace = vi.fn();
    const location = {
      hash: "#task",
      pathname: "/dags/example",
      replace,
      search: "?tab=grid",
    };

    document.head.innerHTML = '<base href="/airflow/">';

    const redirectPromise = redirectToLogin(location);
    const sentinel = Symbol("resolved");

    expect(replace).toHaveBeenCalledWith(
      "/airflow/api/v2/auth/login?next=%2Fdags%2Fexample%3Ftab%3Dgrid%23task",
    );
    await expect(Promise.race([redirectPromise, Promise.resolve(sentinel)])).resolves.toBe(sentinel);
  });
});
