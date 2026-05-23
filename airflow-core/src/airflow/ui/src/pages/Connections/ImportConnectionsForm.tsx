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
import { Box, Button, Center, CloseButton, FileUpload, HStack, Spinner } from "@chakra-ui/react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FiUploadCloud } from "react-icons/fi";
import { LuFileUp } from "react-icons/lu";

import { ErrorAlert } from "src/components/ErrorAlert";
import { RadioCardItem, RadioCardLabel, RadioCardRoot } from "src/components/ui/RadioCard";
import { useImportConnections } from "src/queries/useImportConnections";

import { buildImportConnectionsPayload, type ConnectionImportFile } from "./importConnections";

type ImportConnectionsFormProps = {
  readonly onClose: () => void;
};

const actionIfExistsOptions = (translateImport: (key: string, defaultValue: string) => string) => [
  {
    description: translateImport(
      "connections.import.options.fail.description",
      "Fails the import if any existing connections are detected.",
    ),
    title: translateImport("connections.import.options.fail.title", "Fail"),
    value: "fail",
  },
  {
    description: translateImport(
      "connections.import.options.overwrite.description",
      "Overwrites the connection in case of a conflict.",
    ),
    title: translateImport("connections.import.options.overwrite.title", "Overwrite"),
    value: "overwrite",
  },
  {
    description: translateImport(
      "connections.import.options.skip.description",
      "Skips importing connections that already exist.",
    ),
    title: translateImport("connections.import.options.skip.title", "Skip"),
    value: "skip",
  },
];

const ImportConnectionsForm = ({ onClose }: ImportConnectionsFormProps) => {
  const { t: translate } = useTranslation("admin");
  const { error, isPending, mutate, setError } = useImportConnections({
    onSuccessConfirm: onClose,
  });
  const translateImport = (key: string, defaultValue: string) =>
    translate(key, {
      defaultValue,
    });

  const [actionIfExists, setActionIfExists] = useState<"fail" | "overwrite" | "skip">("fail");
  const [isParsing, setIsParsing] = useState(false);
  const [fileContent, setFileContent] = useState<ConnectionImportFile | undefined>(undefined);

  const onFileChange = (file: File) => {
    setIsParsing(true);
    const reader = new FileReader();

    reader.addEventListener("load", (event) => {
      const text = event.target?.result as string;

      try {
        setFileContent(JSON.parse(text) as ConnectionImportFile);
      } catch {
        setError({
          body: {
            detail: translateImport(
              "connections.import.errorParsingJsonFile",
              'Error parsing JSON file: upload a JSON file containing connections (for example, {"smtp_default": {"conn_type": "smtp"}}).',
            ),
          },
        });
        setFileContent(undefined);
      }

      setIsParsing(false);
    });

    reader.readAsText(file);
  };

  const onSubmit = () => {
    setError(undefined);
    if (fileContent) {
      mutate({ requestBody: buildImportConnectionsPayload(fileContent, actionIfExists) });
    }
  };

  return (
    <>
      <FileUpload.Root
        accept={["application/json"]}
        gap="1"
        maxFiles={1}
        mb={6}
        onFileChange={(files) => {
          if (files.acceptedFiles.length > 0) {
            setError(undefined);
            setFileContent(undefined);
            if (files.acceptedFiles[0]) {
              onFileChange(files.acceptedFiles[0]);
            }
          }
        }}
        required
      >
        <FileUpload.HiddenInput data-testid="upload-input" />
        <FileUpload.Label fontSize="md" mb={3}>
          {translateImport("connections.import.upload", "Upload a JSON File")}
        </FileUpload.Label>
        <FileUpload.Trigger asChild>
          <Button variant="outline">
            <LuFileUp />{" "}
            {translateImport(
              "connections.import.uploadPlaceholder",
              'Upload a JSON file containing connections (for example, {"smtp_default": {"conn_type": "smtp"}})',
            )}
          </Button>
        </FileUpload.Trigger>
        <FileUpload.ItemGroup>
          <FileUpload.Context>
            {({ acceptedFiles }) =>
              acceptedFiles.map((file) => (
                <FileUpload.Item file={file} key={file.name}>
                  <FileUpload.ItemName />
                  <FileUpload.ItemSizeText />
                  <FileUpload.ItemDeleteTrigger
                    asChild
                    onClick={() => {
                      setError(undefined);
                      setFileContent(undefined);
                    }}
                  >
                    <CloseButton size="xs" variant="ghost" />
                  </FileUpload.ItemDeleteTrigger>
                </FileUpload.Item>
              ))
            }
          </FileUpload.Context>
        </FileUpload.ItemGroup>
        {isParsing ? (
          <Center mt={2}>
            <Spinner color="brand.solid" marginRight={2} size="sm" /> Parsing file...
          </Center>
        ) : undefined}
      </FileUpload.Root>
      <RadioCardRoot
        defaultValue="fail"
        mb={6}
        onChange={(event) => {
          const target = event.target as HTMLInputElement;

          setActionIfExists(target.value as "fail" | "overwrite" | "skip");
        }}
      >
        <RadioCardLabel fontSize="md" mb={3}>
          {translateImport("connections.import.conflictResolution", "Select Connection Conflict Resolution")}
        </RadioCardLabel>
        <HStack align="stretch">
          {actionIfExistsOptions(translateImport).map((option) => (
            <RadioCardItem
              description={option.description}
              key={option.value}
              label={option.title}
              value={option.value}
            />
          ))}
        </HStack>
      </RadioCardRoot>
      <ErrorAlert error={error} />
      <Box as="footer" display="flex" justifyContent="flex-end" mt={4}>
        {isPending ? (
          <Box bg="bg.muted" inset="0" pos="absolute">
            <Center h="full">
              <Spinner borderWidth="4px" color="brand.solid" size="xl" />
            </Center>
          </Box>
        ) : undefined}
        <Button disabled={!Boolean(fileContent) || isPending || isParsing} onClick={onSubmit}>
          <FiUploadCloud /> {translateImport("connections.import.button", "Import")}
        </Button>
      </Box>
    </>
  );
};

export default ImportConnectionsForm;
