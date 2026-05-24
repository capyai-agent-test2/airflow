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

import { filterCodeBySection } from "./codeSectionFilter";

const sourceCode = `
from airflow.sdk import dag, task
from airflow.decorators import asset

@dag(schedule="@daily", catchup=False)
def example():
    @task
    def first_task():
        return "ok"

    @asset
    def first_asset():
        return "asset"

with DAG(
    dag_id="legacy_example",
    schedule_interval="@hourly",
    start_date=datetime(2024, 1, 1),
):
    pass
`.trim();

describe("filterCodeBySection", () => {
  it("returns the original source code for the all section", () => {
    expect(filterCodeBySection(sourceCode, "all")).toEqual({ content: sourceCode, matchCount: 0 });
  });

  it("extracts decorated task definitions", () => {
    expect(filterCodeBySection(sourceCode, "tasks")).toEqual({
      content: ['    @task', '    def first_task():', '        return "ok"'].join("\n"),
      matchCount: 1,
    });
  });

  it("extracts decorated asset definitions", () => {
    expect(filterCodeBySection(sourceCode, "assets")).toEqual({
      content: ['    @asset', '    def first_asset():', '        return "asset"'].join("\n"),
      matchCount: 1,
    });
  });

  it("extracts schedule-related configuration blocks", () => {
    expect(filterCodeBySection(sourceCode, "schedule")).toEqual({
      content: [
        '@dag(schedule="@daily", catchup=False)',
        "",
        "with DAG(",
        '    dag_id="legacy_example",',
        '    schedule_interval="@hourly",',
        "    start_date=datetime(2024, 1, 1),",
        "):",
      ].join("\n"),
      matchCount: 2,
    });
  });
});
