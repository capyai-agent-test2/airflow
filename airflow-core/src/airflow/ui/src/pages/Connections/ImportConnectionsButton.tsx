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
import { Button, Heading, useDisclosure, VStack } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { FiUploadCloud } from "react-icons/fi";

import { Dialog } from "src/components/ui";

import ImportConnectionsForm from "./ImportConnectionsForm";

type Props = {
  readonly disabled: boolean;
};

const ImportConnectionsButton = ({ disabled }: Props) => {
  const { t: translate } = useTranslation("admin");
  const { onClose, onOpen, open } = useDisclosure();
  const importTitle = translate("connections.import.title", { defaultValue: "Import Connections" });

  return (
    <>
      <Button disabled={disabled} onClick={onOpen}>
        <FiUploadCloud /> {importTitle}
      </Button>

      <Dialog.Root onOpenChange={onClose} open={open}>
        <Dialog.Content backdrop>
          <Dialog.Header>
            <VStack align="start" gap={4}>
              <Heading size="xl"> {importTitle} </Heading>
            </VStack>
          </Dialog.Header>

          <Dialog.CloseTrigger />

          <Dialog.Body width="full">
            <ImportConnectionsForm onClose={onClose} />
          </Dialog.Body>
        </Dialog.Content>
      </Dialog.Root>
    </>
  );
};

export default ImportConnectionsButton;
