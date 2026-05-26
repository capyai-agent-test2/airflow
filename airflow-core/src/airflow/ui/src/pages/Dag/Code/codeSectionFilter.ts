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

export type CodeSection = "all" | "assets" | "schedule" | "tasks";

type FilteredCode = {
  readonly content: string;
  readonly matchCount: number;
};

const ASSET_DECORATOR_PATTERN = /^(?:\s*)@asset(?:\.\w+)?\b/u;
const TASK_DECORATOR_PATTERN = /^(?:\s*)@task(?:\.\w+)?\b/u;
const SCHEDULE_PATTERN = /\b(?:schedule(?:_interval)?|timetable|start_date|end_date|catchup)\b/u;
const DEFINITION_PATTERN = /^(?:async\s+def|def|class)\b/u;

const getIndentation = (line: string) => /^\s*/u.exec(line)?.[0].length ?? 0;

const joinBlocks = (blocks: Array<string>) => blocks.join("\n\n");
const getBracketDelta = (line: string) =>
  [...line].reduce((balance, character) => {
    if (character === "(" || character === "[" || character === "{") {
      return balance + 1;
    }

    if (character === ")" || character === "]" || character === "}") {
      return balance - 1;
    }

    return balance;
  }, 0);

const getNextDecoratedBlockIndex = (
  lines: Array<string>,
  startIndex: number,
  baseIndentation: number,
) => {
  let endIndex = startIndex + 1;
  let hasSeenDefinition = false;

  while (endIndex < lines.length) {
    const candidateLine = lines[endIndex] ?? "";
    const trimmedLine = candidateLine.trim();

    if (trimmedLine === "") {
      endIndex += 1;
    } else {
      const indentation = getIndentation(candidateLine);
      const isDefinition = DEFINITION_PATTERN.test(trimmedLine);
      const isDecoratorAtSameLevel = indentation === baseIndentation && trimmedLine.startsWith("@");
      const isDefinitionAtSameLevel = indentation === baseIndentation && isDefinition;

      if (isDefinitionAtSameLevel) {
        hasSeenDefinition = true;
        endIndex += 1;
      } else if (!hasSeenDefinition && isDecoratorAtSameLevel) {
        endIndex += 1;
      } else if (hasSeenDefinition && indentation <= baseIndentation) {
        break;
      } else {
        endIndex += 1;
      }
    }
  }

  return endIndex;
};

const extractDecoratedBlocks = (code: string, decoratorPattern: RegExp) => {
  const lines = code.split("\n");
  const blocks: Array<string> = [];

  let index = 0;

  while (index < lines.length) {
    const currentLine = lines[index] ?? "";
    const match = decoratorPattern.exec(currentLine);

    if (match === null) {
      index += 1;
    } else {
      const baseIndentation = getIndentation(currentLine);
      const endIndex = getNextDecoratedBlockIndex(lines, index, baseIndentation);

      blocks.push(lines.slice(index, endIndex).join("\n").trimEnd());
      index = endIndex;
    }
  }

  return blocks;
};

const extractScheduleBlocks = (code: string) => {
  const lines = code.split("\n");
  const blocks: Array<string> = [];
  const seenRanges = new Set<string>();

  lines.forEach((line, lineIndex) => {
    if (!SCHEDULE_PATTERN.test(line)) {
      return;
    }

    const trimmedLine = line.trim();

    if (trimmedLine.startsWith("@dag(")) {
      const decoratorRangeKey = `${lineIndex}:${lineIndex}`;

      if (!seenRanges.has(decoratorRangeKey)) {
        seenRanges.add(decoratorRangeKey);
        blocks.push(trimmedLine);
      }

      return;
    }

    const indentation = getIndentation(line);
    let startIndex = lineIndex;
    let endIndex = lineIndex + 1;

    while (startIndex > 0) {
      const previousLine = lines[startIndex - 1] ?? "";
      const trimmedPreviousLine = previousLine.trim();

      if (trimmedPreviousLine === "") {
        break;
      }

      if (getIndentation(previousLine) < indentation) {
        if (
          trimmedPreviousLine.endsWith("(") ||
          trimmedPreviousLine.startsWith("@dag(") ||
          trimmedPreviousLine.startsWith("with DAG(")
        ) {
          startIndex -= 1;
        }

        break;
      }

      startIndex -= 1;
    }

    let bracketBalance = lines
      .slice(startIndex, endIndex)
      .reduce((balance, currentLine) => balance + getBracketDelta(currentLine), 0);

    while (endIndex < lines.length) {
      const nextLine = lines[endIndex] ?? "";
      const trimmedNextLine = nextLine.trim();

      if (trimmedNextLine === "") {
        break;
      }

      const nextIndentation = getIndentation(nextLine);
      const isClosingContinuationLine =
        bracketBalance > 0 && (trimmedNextLine.startsWith(")") || trimmedNextLine.startsWith("]") || trimmedNextLine.startsWith("}"));
      const startsNestedBody = nextIndentation > indentation && bracketBalance <= 0;

      if (nextIndentation < indentation || startsNestedBody || (nextIndentation === indentation && bracketBalance <= 0)) {
        if (isClosingContinuationLine) {
          endIndex += 1;
        }

        break;
      }

      bracketBalance += getBracketDelta(nextLine);
      endIndex += 1;
    }

    const rangeKey = `${startIndex}:${endIndex}`;

    if (!seenRanges.has(rangeKey)) {
      seenRanges.add(rangeKey);
      blocks.push(lines.slice(startIndex, endIndex).join("\n").trimEnd());
    }
  });

  return blocks;
};

export const filterCodeBySection = (code: string, section: CodeSection): FilteredCode => {
  if (section === "all") {
    return { content: code, matchCount: 0 };
  }

  const blocks =
    section === "tasks"
      ? extractDecoratedBlocks(code, TASK_DECORATOR_PATTERN)
      : section === "assets"
        ? extractDecoratedBlocks(code, ASSET_DECORATOR_PATTERN)
        : extractScheduleBlocks(code);

  return { content: joinBlocks(blocks), matchCount: blocks.length };
};
