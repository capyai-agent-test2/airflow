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

import type { ParamSchema, ParamsSpec } from "src/queries/useDagParams";

import { mergeConnectionExtraWithWidgetValues } from "./connectionFormExtra";

const buildSchema = (type: Array<string>): ParamSchema => ({
  const: undefined,
  description_md: undefined,
  enum: undefined,
  examples: undefined,
  format: undefined,
  items: undefined,
  maximum: undefined,
  maxLength: undefined,
  minimum: undefined,
  minLength: undefined,
  section: undefined,
  title: undefined,
  type,
  values_display: undefined,
});

describe("mergeConnectionExtraWithWidgetValues", () => {
  it("preserves raw extras when string and boolean widgets are unset", () => {
    const paramsDict: ParamsSpec = {
      account: { description: null, schema: buildSchema(["string", "null"]), value: "" },
      insecure_mode: { description: null, schema: buildSchema(["boolean", "null"]), value: false },
    };

    expect(mergeConnectionExtraWithWidgetValues('{"account":"1234"}', paramsDict)).toBe('{\n  "account": "1234"\n}');
  });

  it("writes widget values when they are explicitly set", () => {
    const paramsDict: ParamsSpec = {
      account: { description: null, schema: buildSchema(["string", "null"]), value: "acct-1" },
      insecure_mode: { description: null, schema: buildSchema(["boolean", "null"]), value: true },
    };

    expect(mergeConnectionExtraWithWidgetValues("{}", paramsDict)).toBe(
      '{\n  "account": "acct-1",\n  "insecure_mode": true\n}',
    );
  });

  it("leaves non-json extras unchanged", () => {
    expect(mergeConnectionExtraWithWidgetValues("not-json", {})).toBe("not-json");
  });
});
