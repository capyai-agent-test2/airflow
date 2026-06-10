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

import { createTheme, normalizeLegacyColorFunctions } from "./theme";

describe("normalizeLegacyColorFunctions", () => {
  it("converts nested unsupported CSS color functions to hex", () => {
    const normalized = normalizeLegacyColorFunctions({
      colors: {
        black: { value: "oklch(0.23185 0.0323 266.44)" },
        brand: { "500": { value: "oklch(0.575 0.08 257.759)" } },
      },
    });

    expect(normalized).toEqual({
      colors: {
        black: { value: "#161d2d" },
        brand: { "500": { value: "#5b7aa8" } },
      },
    });
  });

  it("leaves compatible CSS values and token references unchanged", () => {
    const normalized = normalizeLegacyColorFunctions({
      colors: {
        brand: { "500": { value: "#5b7aa8" } },
      },
      semanticTokens: {
        colors: {
          brand: { solid: { value: "{colors.brand.500}" } },
        },
      },
    });

    expect(normalized).toEqual({
      colors: {
        brand: { "500": { value: "#5b7aa8" } },
      },
      semanticTokens: {
        colors: {
          brand: { solid: { value: "{colors.brand.500}" } },
        },
      },
    });
  });
});

describe("createTheme", () => {
  it("normalizes the default theme before Chakra generates token CSS", () => {
    const system = createTheme();

    expect(system.token("colors.black")).toBe("#161d2d");
    expect(system.token("colors.brand.500")).toBe("#5b7aa8");
  });

  it("normalizes user-provided theme color tokens", () => {
    const system = createTheme({
      tokens: {
        colors: {
          brand: {
            "500": { value: "oklch(0.575 0.08 257.759)" },
          },
        },
      },
    });

    expect(system.token("colors.brand.500")).toBe("#5b7aa8");
  });
});
