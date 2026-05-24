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
import {
  Box,
  Button,
  CloseButton,
  createListCollection,
  Heading,
  HStack,
  Input,
  InputGroup,
  Link,
  Text,
  VStack,
  type SelectValueChangeDetails,
} from "@chakra-ui/react";
import type { editor, Range } from "monaco-editor";
import { useEffect, useRef, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import { useTranslation } from "react-i18next";
import { FiChevronDown, FiChevronUp, FiSearch } from "react-icons/fi";
import { useParams } from "react-router-dom";

import {
  useDagServiceGetDagDetails,
  useDagSourceServiceGetDagSource,
  useDagVersionServiceGetDagVersion,
  useDagVersionServiceGetDagVersions,
} from "openapi/queries";
import type { ApiError } from "openapi/requests/core/ApiError";
import type { DAGSourceResponse } from "openapi/requests/types.gen";
import { DagVersionSelect } from "src/components/DagVersionSelect";
import { ErrorAlert } from "src/components/ErrorAlert";
import Editor, { type EditorProps, type OnMount } from "src/components/MonacoEditor";
import Time from "src/components/Time";
import { ClipboardRoot, ClipboardButton, IconButton, ProgressBar, Select, Tooltip } from "src/components/ui";
import { useMonacoTheme } from "src/context/colorMode";
import useSelectedVersion from "src/hooks/useSelectedVersion";
import { useConfig } from "src/queries/useConfig";
import { renderDuration } from "src/utils";

import { CodeDiffViewer } from "./CodeDiffViewer";
import { FileLocation } from "./FileLocation";
import { VersionCompareSelect } from "./VersionCompareSelect";
import { filterCodeBySection, type CodeSection } from "./codeSectionFilter";

const sectionOptions = (translate: ReturnType<typeof useTranslation>["t"]) =>
  createListCollection({
    items: [
      { label: translate("common:expression.all"), value: "all" },
      { label: translate("code.sections.tasks"), value: "tasks" },
      { label: translate("code.sections.assets"), value: "assets" },
      { label: translate("code.sections.schedule"), value: "schedule" },
    ],
  });

export const Code = () => {
  const { t: translate } = useTranslation(["dag", "common"]);
  const { dagId } = useParams();

  const selectedVersion = useSelectedVersion();

  const {
    data: dag,
    error,
    isLoading,
  } = useDagServiceGetDagDetails({
    dagId: dagId ?? "",
  });

  const { data: dagVersion } = useDagVersionServiceGetDagVersion(
    {
      dagId: dagId ?? "",
      versionNumber: selectedVersion ?? 1,
    },
    undefined,
    { enabled: dag !== undefined && selectedVersion !== undefined },
  );

  const { data: dagVersions } = useDagVersionServiceGetDagVersions({
    dagId: dagId ?? "",
  });

  const defaultWrap = Boolean(useConfig("default_wrap"));

  const [wrap, setWrap] = useState(defaultWrap);
  const [compareVersionNumber, setCompareVersionNumber] = useState<number | undefined>(undefined);
  const [isCompareDropdownOpen, setIsCompareDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentSearchMatch, setCurrentSearchMatch] = useState(0);
  const [searchMatches, setSearchMatches] = useState<Array<Range>>([]);
  const [section, setSection] = useState<CodeSection>("all");

  const isDiffMode = compareVersionNumber !== undefined;

  const {
    data: code,
    error: codeError,
    isLoading: isCodeLoading,
  } = useDagSourceServiceGetDagSource<DAGSourceResponse, ApiError | null>({
    dagId: dagId ?? "",
    versionNumber: selectedVersion,
  });

  const {
    data: compareCode,
    error: compareCodeError,
    isLoading: isCompareCodeLoading,
  } = useDagSourceServiceGetDagSource<DAGSourceResponse, ApiError | null>(
    {
      dagId: dagId ?? "",
      versionNumber: compareVersionNumber,
    },
    undefined,
    { enabled: isDiffMode },
  );

  const toggleWrap = () => setWrap(!wrap);
  const toggleCompareDropdown = () => setIsCompareDropdownOpen(!isCompareDropdownOpen);
  const exitDiffMode = () => {
    setCompareVersionNumber(undefined);
    setIsCompareDropdownOpen(false);
  };
  const handleVersionChange = (versionNumber: number) => {
    setCompareVersionNumber(versionNumber);
    setIsCompareDropdownOpen(false);
  };

  const { beforeMount, theme } = useMonacoTheme();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const decorationsCollectionRef = useRef<editor.IEditorDecorationsCollection | null>(null);

  useHotkeys("w", toggleWrap);

  const editorOptions: EditorProps["options"] = {
    automaticLayout: true,
    contextmenu: false,
    find: {
      addExtraSpaceOnTop: false,
      autoFindInSelection: "never" as const,
      seedSearchStringFromSelection: "always" as const,
    },
    fontSize: 14,
    glyphMargin: false,
    lineDecorationsWidth: 20,
    lineNumbers: "on",
    minimap: { enabled: false },
    readOnly: true,
    renderLineHighlight: "none",
    wordWrap: wrap ? "on" : "off",
  };

  const hasMultipleVersions = (dagVersions?.dag_versions.length ?? 0) >= 2;
  const sourceCode =
    codeError?.status === 404 && !Boolean(code?.content) ? translate("code.noCode") : (code?.content ?? "");
  const filteredCode = filterCodeBySection(sourceCode, section);
  const displayedCode = filteredCode.content;
  const activeSectionLabel =
    section === "all"
      ? undefined
      : translate("code.sectionMatches", {
          count: filteredCode.matchCount,
          section: sectionOptions(translate).items.find((option) => option.value === section)?.label.toLowerCase(),
        });

  const updateSearchDecorations = (matches: Array<Range>, activeMatchIndex: number) => {
    if (decorationsCollectionRef.current === null) {
      return;
    }

    decorationsCollectionRef.current.set(
      matches.map((range, index) => ({
        options: { className: index === activeMatchIndex ? "code-search-match-current" : "code-search-match" },
        range,
      })),
    );
  };

  useEffect(() => {
    const model = editorRef.current?.getModel();

    if (model === null || model === undefined) {
      setSearchMatches([]);
      setCurrentSearchMatch(0);

      return;
    }

    if (searchQuery === "") {
      setSearchMatches([]);
      setCurrentSearchMatch(0);
      decorationsCollectionRef.current?.clear();

      return;
    }

    const matches = model
      .findMatches(searchQuery, true, false, false, null, true)
      .map((match) => match.range);

    setSearchMatches(matches);
    setCurrentSearchMatch(0);
    updateSearchDecorations(matches, 0);

    if (matches[0] !== undefined) {
      editorRef.current?.setSelection(matches[0]);
      editorRef.current?.revealRangeInCenter(matches[0]);
    }
  }, [displayedCode, searchQuery]);

  const navigateToSearchMatch = (direction: "next" | "previous") => {
    if (searchMatches.length === 0) {
      return;
    }

    const nextMatchIndex =
      direction === "next"
        ? (currentSearchMatch + 1) % searchMatches.length
        : (currentSearchMatch - 1 + searchMatches.length) % searchMatches.length;
    const range = searchMatches[nextMatchIndex];

    setCurrentSearchMatch(nextMatchIndex);
    updateSearchDecorations(searchMatches, nextMatchIndex);

    if (range !== undefined) {
      editorRef.current?.setSelection(range);
      editorRef.current?.revealRangeInCenter(range);
      editorRef.current?.focus();
    }
  };

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor;
    decorationsCollectionRef.current = editor.createDecorationsCollection();
  };

  const handleSectionChange = (
    event: SelectValueChangeDetails<{ label: string; value: Array<CodeSection> }>,
  ) => {
    const [nextSection] = event.value;

    if (nextSection !== undefined) {
      setSection(nextSection as CodeSection);
    }
  };

  return (
    <Box h="100%" overflow="hidden">
      <HStack justifyContent="space-between" mt={2}>
        <HStack gap={5}>
          {dag?.last_parsed_time !== undefined && (
            <Heading as="h4" fontSize="14px" size="md">
              {translate("code.parsedAt")} <Time datetime={dag.last_parsed_time} />
            </Heading>
          )}
          {dag?.last_parse_duration !== undefined && (
            <Heading as="h4" fontSize="14px" size="md">
              {translate("code.parseDuration")} {renderDuration(dag.last_parse_duration)}
            </Heading>
          )}

          {dagVersion !== undefined && dagVersion.bundle_version !== null ? (
            <Heading as="h4" fontSize="14px" size="md" wordBreak="break-word">
              {translate("dagDetails.bundleVersion")}
              {": "}
              {dagVersion.bundle_url === null ? (
                dagVersion.bundle_version
              ) : (
                <Link
                  aria-label={translate("code.bundleUrl")}
                  color="fg.info"
                  href={dagVersion.bundle_url}
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  {dagVersion.bundle_version}
                </Link>
              )}
            </Heading>
          ) : undefined}
        </HStack>
        <VStack gap={2} position="relative">
          <HStack flexWrap="wrap" gap={2}>
            <DagVersionSelect showLabel={false} />
            {isDiffMode ? undefined : (
              <HStack flexWrap="wrap" gap={2}>
                <InputGroup
                  endElement={
                    searchQuery ? (
                      <HStack gap={0.5}>
                        <Text color="fg.muted" fontSize="xs" whiteSpace="nowrap">
                          {searchMatches.length > 0
                            ? translate("logs.search.matchCount", {
                                current: currentSearchMatch + 1,
                                total: searchMatches.length,
                              })
                            : translate("logs.search.noMatches")}
                        </Text>
                        <IconButton
                          aria-label={translate("code.search.previousMatch")}
                          disabled={searchMatches.length === 0}
                          onClick={() => navigateToSearchMatch("previous")}
                          size="2xs"
                        >
                          <FiChevronUp />
                        </IconButton>
                        <IconButton
                          aria-label={translate("code.search.nextMatch")}
                          disabled={searchMatches.length === 0}
                          onClick={() => navigateToSearchMatch("next")}
                          size="2xs"
                        >
                          <FiChevronDown />
                        </IconButton>
                        <CloseButton onClick={() => setSearchQuery("")} size="2xs" />
                      </HStack>
                    ) : undefined
                  }
                  startElement={<FiSearch />}
                >
                  <Input
                    aria-label={translate("code.search.label")}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder={translate("code.search.placeholder")}
                    size="sm"
                    value={searchQuery}
                    width="240px"
                  />
                </InputGroup>
                <Select.Root
                  collection={sectionOptions(translate)}
                  onValueChange={handleSectionChange}
                  positioning={{ sameWidth: false }}
                  size="sm"
                  value={[section]}
                  width="180px"
                >
                  <Select.Control>
                    <Select.Trigger aria-label={translate("code.sections.label")}>
                      <Select.ValueText placeholder={translate("code.sections.label")} />
                    </Select.Trigger>
                    <Select.IndicatorGroup>
                      <Select.Indicator />
                    </Select.IndicatorGroup>
                  </Select.Control>
                  <Select.Positioner>
                    <Select.Content>
                      {sectionOptions(translate).items.map((option) => (
                        <Select.Item item={option} key={option.value}>
                          {option.label}
                        </Select.Item>
                      ))}
                    </Select.Content>
                  </Select.Positioner>
                </Select.Root>
              </HStack>
            )}
            <ClipboardRoot value={code?.content ?? ""}>
              <ClipboardButton />
            </ClipboardRoot>
            <Tooltip
              closeDelay={100}
              content={translate("common:wrap.tooltip", { hotkey: "w" })}
              openDelay={100}
            >
              <Button
                aria-label={translate(`common:wrap.${wrap ? "un" : ""}wrap`)}
                onClick={toggleWrap}
                variant="outline"
              >
                {translate(`common:wrap.${wrap ? "un" : ""}wrap`)}
              </Button>
            </Tooltip>
            {hasMultipleVersions ? (
              <Button
                aria-label={translate("common:diff")}
                onClick={toggleCompareDropdown}
                variant={isCompareDropdownOpen ? "solid" : "outline"}
              >
                {translate("common:diff")}
              </Button>
            ) : undefined}
            {isDiffMode ? (
              <Button aria-label={translate("common:diffExit")} onClick={exitDiffMode} variant="solid">
                {translate("common:diffExit")}
              </Button>
            ) : undefined}
          </HStack>
          {isCompareDropdownOpen ? (
            <Box
              bg="bg.panel"
              borderRadius="md"
              insetInlineEnd={0}
              mt={4}
              p={2}
              position="absolute"
              shadow="sm"
              top="100%"
              zIndex={10}
            >
              <VersionCompareSelect
                label={translate("common:diffCompareWith")}
                onVersionChange={handleVersionChange}
                placeholder={translate("common:diffSelectVersionToCompare")}
                selectedVersionNumber={compareVersionNumber}
              />
            </Box>
          ) : undefined}
        </VStack>
      </HStack>
      {/* We want to show an empty state on 404 instead of an error */}
      <ErrorAlert
        error={
          error ??
          (codeError?.status === 404 ? undefined : codeError) ??
          (compareCodeError?.status === 404 ? undefined : compareCodeError)
        }
      />
      <ProgressBar
        size="xs"
        visibility={isLoading || isCodeLoading || isCompareCodeLoading ? "visible" : "hidden"}
      />

      {isDiffMode ? (
        <Box dir="ltr" height="full">
          {dag?.fileloc !== undefined && (
            <FileLocation fileloc={dag.fileloc} relativeFileloc={dag.relative_fileloc} />
          )}
          <CodeDiffViewer
            modifiedCode={
              codeError?.status === 404 && !Boolean(code?.content)
                ? translate("code.noCode")
                : (code?.content ?? "")
            }
            originalCode={
              compareCodeError?.status === 404 && !Boolean(compareCode?.content)
                ? translate("code.noCode")
                : (compareCode?.content ?? "")
            }
          />
        </Box>
      ) : (
        <Box
          css={{
            "& *::selection": {
              bg: "gray.emphasized",
            },
            "& .code-search-match": {
              background: "var(--chakra-colors-yellow-subtle)",
            },
            "& .code-search-match-current": {
              background: "var(--chakra-colors-yellow-emphasized)",
            },
          }}
          dir="ltr"
          fontSize="14px"
          height="full"
        >
          {dag?.fileloc !== undefined && (
            <FileLocation fileloc={dag.fileloc} relativeFileloc={dag.relative_fileloc} />
          )}
          {activeSectionLabel === undefined ? undefined : (
            <Text color="fg.muted" fontSize="sm" mb={2}>
              {activeSectionLabel}
            </Text>
          )}
          <Editor
            beforeMount={beforeMount}
            language="python"
            onMount={handleEditorMount}
            options={editorOptions}
            theme={theme}
            value={displayedCode}
          />
        </Box>
      )}
    </Box>
  );
};
