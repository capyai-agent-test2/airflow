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
import { fireEvent, render, screen } from "@testing-library/react";
import { useEffect, useRef } from "react";
import { describe, expect, it, vi } from "vitest";

import { Wrapper } from "src/utils/Wrapper";

import { Code } from "./Code";

const sourceCode = `
@dag(schedule="@daily", catchup=False)
def example():
    @task
    def first_task():
        return "task"

    @asset
    def first_asset():
        return "asset"
`.trim();

const mockTranslate = (translationKey: string, options?: Record<string, number | string | undefined>) => {
  if (translationKey === "logs.search.matchCount") {
    return `${options?.current} of ${options?.total}`;
  }
  if (translationKey === "logs.search.noMatches") {
    return "No matches";
  }
  if (translationKey === "common:expression.all") {
    return "All";
  }
  if (translationKey === "code.sectionMatches") {
    return `${options?.count} matching ${options?.section} sections`;
  }

  const translations: Record<string, string> = {
    "code.bundleUrl": "Bundle Url",
    "code.noCode": "No Code Found",
    "code.parsedAt": "Parsed at:",
    "code.parseDuration": "Parse Duration:",
    "code.search.label": "Search code",
    "code.search.nextMatch": "Next match",
    "code.search.placeholder": "Search code...",
    "code.search.previousMatch": "Previous match",
    "code.sections.assets": "Asset definitions",
    "code.sections.label": "Section filter",
    "code.sections.schedule": "Schedule config",
    "code.sections.tasks": "Task definitions",
    "common:wrap.tooltip": "Press w to toggle wrap",
    "common:wrap.wrap": "Wrap",
  };

  return translations[translationKey] ?? translationKey;
};

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");

  return {
    ...actual,
    useParams: () => ({ dagId: "example" }),
  };
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ "t": mockTranslate }),
}));

vi.mock("src/hooks/useSelectedVersion", () => ({
  default: vi.fn(() => 1),
}));

vi.mock("src/queries/useConfig", () => ({
  useConfig: vi.fn(() => false),
}));

vi.mock("src/context/colorMode", () => ({
  useMonacoTheme: vi.fn(() => ({ beforeMount: vi.fn(), theme: "light" })),
}));

vi.mock("openapi/queries", () => ({
  useDagServiceGetDagDetails: vi.fn(() => ({
    data: {
      fileloc: "/opt/airflow/dags/example.py",
      last_parse_duration: 1.2,
      last_parsed_time: "2025-01-01T00:00:00Z",
      relative_fileloc: "example.py",
    },
    error: undefined,
    isLoading: false,
  })),
  useDagSourceServiceGetDagSource: vi.fn(() => ({
    data: { content: sourceCode },
    error: undefined,
    isLoading: false,
  })),
  useDagVersionServiceGetDagVersion: vi.fn(() => ({ data: undefined })),
  useDagVersionServiceGetDagVersions: vi.fn(() => ({ data: { dag_versions: [] } })),
}));

vi.mock("src/components/DagVersionSelect", () => ({
  DagVersionSelect: () => <div>DagVersionSelect</div>,
}));

vi.mock("./FileLocation", () => ({
  FileLocation: ({ fileloc }: { readonly fileloc: string }) => <div>{fileloc}</div>,
}));

vi.mock("./VersionCompareSelect", () => ({
  VersionCompareSelect: () => <div>VersionCompareSelect</div>,
}));

vi.mock("./CodeDiffViewer", () => ({
  CodeDiffViewer: () => <div>CodeDiffViewer</div>,
}));

vi.mock("src/components/MonacoEditor", () => ({
  __esModule: true,
  default: function MockMonacoEditor({
    onMount,
    value,
  }: {
    readonly onMount?: (editor: {
      readonly createDecorationsCollection: () => { clear: () => void; set: () => void };
      readonly focus: () => void;
      readonly getModel: () => { findMatches: (query: string) => Array<{ range: { endColumn: number; endLineNumber: number; startColumn: number; startLineNumber: number } }> };
      readonly revealRangeInCenter: () => void;
      readonly setSelection: () => void;
    }) => void;
    readonly value: string;
  }) {
    const valueRef = useRef(value);

    valueRef.current = value;

    useEffect(() => {
      onMount?.({
        createDecorationsCollection: () => ({ clear: vi.fn(), set: vi.fn() }),
        focus: vi.fn(),
        getModel: () => ({
          findMatches: (query: string) => {
            const matches: Array<{
              range: { endColumn: number; endLineNumber: number; startColumn: number; startLineNumber: number };
            }> = [];
            const pattern = new RegExp(query, "giu");
            let match = pattern.exec(valueRef.current);

            while (match !== null) {
              const startOffset = match.index;
              const before = valueRef.current.slice(0, startOffset);
              const lineParts = before.split("\n");
              const startLineNumber = lineParts.length;
              const startColumn = (lineParts.at(-1)?.length ?? 0) + 1;
              const endColumn = startColumn + match[0].length;

              matches.push({ range: { endColumn, endLineNumber: startLineNumber, startColumn, startLineNumber } });
              match = pattern.exec(valueRef.current);
            }

            return matches;
          },
        }),
        revealRangeInCenter: vi.fn(),
        setSelection: vi.fn(),
      });
    }, [onMount]);

    return <pre data-testid="code-editor">{value}</pre>;
  },
}));

describe("Code", () => {
  it("renders a search input and updates the match count", async () => {
    render(<Code />, { wrapper: Wrapper });

    fireEvent.change(screen.getByLabelText("Search code"), { target: { value: "task" } });

    expect(await screen.findByText("1 of 3")).toBeInTheDocument();
  });
});
