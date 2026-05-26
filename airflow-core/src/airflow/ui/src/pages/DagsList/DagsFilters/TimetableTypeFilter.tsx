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
import { CloseButton, Input, InputGroup } from "@chakra-ui/react";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { FiSearch } from "react-icons/fi";
import { useDebouncedCallback } from "use-debounce";

const debounceDelay = 200;

type Props = {
  readonly onChange: (value: string) => void;
  readonly value: string;
};

export const TimetableTypeFilter = ({ onChange, value }: Props) => {
  const { t: translate } = useTranslation("common");
  const lastSentValue = useRef(value);
  const handleInputChange = useDebouncedCallback((nextValue: string) => {
    lastSentValue.current = nextValue;
    onChange(nextValue);
  }, debounceDelay);
  const [currentValue, setCurrentValue] = useState(value);

  useEffect(() => {
    if (value !== lastSentValue.current) {
      setCurrentValue(value);
      lastSentValue.current = value;
    }
  }, [value]);

  const onTimetableTypeChange = (event: ChangeEvent<HTMLInputElement>) => {
    setCurrentValue(event.target.value);
    handleInputChange(event.target.value);
  };

  const clearFilter = () => {
    handleInputChange.cancel();
    lastSentValue.current = "";
    setCurrentValue("");
    onChange("");
  };

  return (
    <InputGroup
      colorPalette="brand"
      endElement={
        Boolean(currentValue) ? (
          <CloseButton
            aria-label={translate("search.clear")}
            data-testid="clear-timetable-type-filter"
            onClick={clearFilter}
            size="xs"
          />
        ) : undefined
      }
      maxWidth="320px"
      startElement={<FiSearch />}
    >
      <Input
        aria-label={translate("table.filterByTimetableType")}
        data-testid="timetable-type-filter"
        onChange={onTimetableTypeChange}
        placeholder={translate("table.timetableTypePlaceholder")}
        value={currentValue}
      />
    </InputGroup>
  );
};
