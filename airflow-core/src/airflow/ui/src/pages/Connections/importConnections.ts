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
import type { BulkBody_ConnectionBody_, ConnectionBody } from "openapi/requests/types.gen";

type ConnectionImportFile = Record<string, Omit<ConnectionBody, "connection_id">>;

export const buildImportConnectionsPayload = (
  fileContent: ConnectionImportFile,
  actionIfExists: "fail" | "overwrite" | "skip",
): BulkBody_ConnectionBody_ => ({
  actions: [
    {
      action: "create" as const,
      action_on_existence: actionIfExists,
      entities: Object.entries(fileContent).map(([connectionId, value]) => ({
        conn_type: value.conn_type,
        connection_id: connectionId,
        description: value.description,
        extra: value.extra,
        host: value.host,
        login: value.login,
        password: value.password,
        port: value.port,
        schema: value.schema,
        team_name: value.team_name,
      })),
    },
  ],
});

export type { ConnectionImportFile };
