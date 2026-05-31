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
import supportedVersions from "../../../../../docs/installation/supported-versions.rst?raw";

const AIRFLOW_DOCS_BASE_URL = "https://airflow.apache.org/docs/apache-airflow";
const STABLE_DOCS_VERSION = "stable";

const currentStableAirflowVersion = /^\s*\d+(?:\.\d+)?\s+(?<version>\d+\.\d+\.\d+)\s+/mu.exec(
  supportedVersions,
)?.groups?.version;

const getReleaseVersionParts = (version: string): [number, number, number] | undefined => {
  const versionParts = /^(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)$/u.exec(version);

  if (versionParts === null) {
    return undefined;
  }

  const { major, minor, patch } = versionParts.groups ?? {};

  if (major === undefined || minor === undefined || patch === undefined) {
    return undefined;
  }

  return [Number(major), Number(minor), Number(patch)];
};

const compareReleaseVersions = (left: [number, number, number], right: [number, number, number]) => {
  for (const [index, part] of left.entries()) {
    const otherPart = right[index];

    if (otherPart !== undefined && part !== otherPart) {
      return part - otherPart;
    }
  }

  return 0;
};

const isPublishedReleaseVersion = (version: string) => {
  const releaseVersionParts = getReleaseVersionParts(version);
  const stableVersionParts =
    currentStableAirflowVersion === undefined
      ? undefined
      : getReleaseVersionParts(currentStableAirflowVersion);

  if (releaseVersionParts === undefined || stableVersionParts === undefined) {
    return false;
  }

  return compareReleaseVersions(releaseVersionParts, stableVersionParts) <= 0;
};

export const getAirflowDocsUrl = (version: string | undefined, path: string) => {
  const docsVersion =
    version === undefined || !isPublishedReleaseVersion(version) ? STABLE_DOCS_VERSION : version;

  return `${AIRFLOW_DOCS_BASE_URL}/${docsVersion}/${path}`;
};
