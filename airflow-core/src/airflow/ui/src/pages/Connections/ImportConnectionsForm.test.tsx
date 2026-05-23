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
import { describe, expect, it } from "vitest";

import { buildImportConnectionsPayload } from "./importConnections";

describe("buildImportConnectionsPayload", () => {
  it("builds a bulk create payload from imported connection json", () => {
    const payload = buildImportConnectionsPayload(
      {
        smtp_default: {
          conn_type: "smtp",
          description: "Mail server",
          extra: '{"timeout": 30}',
          host: "smtp.example.com",
          login: "mailer",
          password: "secret",
          port: 587,
          schema: "tls",
        },
      },
      "overwrite",
    );

    expect(payload).toEqual({
      actions: [
        {
          action: "create",
          action_on_existence: "overwrite",
          entities: [
            {
              conn_type: "smtp",
              connection_id: "smtp_default",
              description: "Mail server",
              extra: '{"timeout": 30}',
              host: "smtp.example.com",
              login: "mailer",
              password: "secret",
              port: 587,
              schema: "tls",
              team_name: undefined,
            },
          ],
        },
      ],
    });
  });
});
