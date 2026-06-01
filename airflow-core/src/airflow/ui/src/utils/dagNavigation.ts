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

const DAG_TABS = new Set([
  "backfills",
  "calendar",
  "code",
  "details",
  "events",
  "required_actions",
  "runs",
  "tasks",
]);
const RUN_TABS = new Set(["asset_events", "code", "details", "events", "required_actions"]);

const getSegments = (pathname: string) => pathname.split("/").filter(Boolean).map(decodeURIComponent);

const findDagSegments = (pathname: string) => {
  const segments = getSegments(pathname);
  const dagsIndex = segments.indexOf("dags");

  return dagsIndex === -1 ? [] : segments.slice(dagsIndex + 2);
};

const findRunTab = (pathname: string) => {
  const segments = findDagSegments(pathname);

  if (segments[0] === "runs" && segments[2] !== undefined && RUN_TABS.has(segments[2])) {
    return segments[2];
  }

  return undefined;
};

export const buildDagNavigationPath = ({ dagId, pathname }: { dagId: string; pathname: string }) => {
  const segments = findDagSegments(pathname);
  const tab = segments[0] === "runs" ? segments[2] : segments[0];

  return tab !== undefined && DAG_TABS.has(tab) ? `/dags/${dagId}/${tab}` : `/dags/${dagId}`;
};

export const buildRunNavigationPath = ({
  dagId,
  pathname,
  runId,
  taskId,
}: {
  dagId: string;
  pathname: string;
  runId: string;
  taskId?: string;
}) => {
  const taskPath = taskId === undefined ? undefined : `tasks/${taskId}`;
  const tab = taskPath ?? findRunTab(pathname);
  const pathSegments = ["dags", dagId, "runs", runId, tab].filter((segment) => segment !== undefined);

  return `/${pathSegments.join("/")}`;
};
