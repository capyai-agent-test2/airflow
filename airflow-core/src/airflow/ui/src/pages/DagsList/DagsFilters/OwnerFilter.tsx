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
import { Box, Field } from "@chakra-ui/react";
import { CreatableSelect, type MultiValue } from "chakra-react-select";
import { useTranslation } from "react-i18next";

type OwnerOption = {
  label: string;
  value: string;
};

type Props = {
  readonly onSelectOwnersChange: (owners: MultiValue<OwnerOption>) => void;
  readonly selectedOwners: Array<string>;
};

export const OwnerFilter = ({ onSelectOwnersChange, selectedOwners }: Props) => {
  const { t: translate } = useTranslation(["common", "dags"]);
  const selectedOwnerOptions = selectedOwners.map((owner) => ({
    label: owner,
    value: owner,
  }));

  return (
    <Box data-testid="owner-filter" maxWidth="300px" minWidth="140px">
      <Field.Root>
        <CreatableSelect
          aria-label={translate("common:owner")}
          chakraStyles={{
            clearIndicator: (provided) => ({
              ...provided,
              color: "gray.fg",
            }),
            container: (provided) => ({
              ...provided,
              maxWidth: 300,
              minWidth: 140,
            }),
            control: (provided) => ({
              ...provided,
              colorPalette: "brand",
            }),
            menu: (provided) => ({
              ...provided,
              zIndex: 2,
            }),
          }}
          isClearable
          isMulti
          onChange={onSelectOwnersChange}
          options={selectedOwnerOptions}
          placeholder={translate("dags:filters.owner.placeholder")}
          value={selectedOwnerOptions}
        />
      </Field.Root>
    </Box>
  );
};
