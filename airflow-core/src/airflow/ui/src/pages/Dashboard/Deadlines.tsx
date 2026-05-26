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
import { Badge, Box, Flex, Heading, HStack, Separator, Skeleton, Text, VStack } from "@chakra-ui/react";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { FiAlertTriangle, FiClock } from "react-icons/fi";
import { Link } from "react-router-dom";

import { useDeadlinesServiceGetDeadlines } from "openapi/queries";
import type { DeadlineResponse } from "openapi/requests/types.gen";
import { ErrorAlert } from "src/components/ErrorAlert";
import Time from "src/components/Time";
import { useAutoRefresh } from "src/utils";

const LIMIT = 5;

const buildDeadlineFilters = () => {
  const now = dayjs();

  return {
    missedSince: now.subtract(1, "day").toISOString(),
    pendingFrom: now.toISOString(),
  };
};

type DeadlineListProps = {
  readonly deadlines: Array<DeadlineResponse>;
  readonly emptyText: string;
  readonly isLoading: boolean;
};

const DeadlineList = ({ deadlines, emptyText, isLoading }: DeadlineListProps) => {
  const { t: translate } = useTranslation("dag");

  if (isLoading) {
    return (
      <VStack>
        {Array.from({ length: 3 }).map((_, idx) => (
          // eslint-disable-next-line react/no-array-index-key
          <Skeleton height="56px" key={idx} width="100%" />
        ))}
      </VStack>
    );
  }

  if (deadlines.length === 0) {
    return (
      <Text color="fg.muted" fontSize="sm">
        {emptyText}
      </Text>
    );
  }

  return (
    <VStack alignItems="stretch" gap={0} separator={<Separator />}>
      {deadlines.map((deadline) => (
        <Flex alignItems="flex-start" justifyContent="space-between" key={deadline.id}>
          <VStack alignItems="flex-start" gap={0.5}>
            <HStack gap={1}>
              <Badge colorPalette={deadline.missed ? "red" : "blue"} size="sm" variant="solid">
                {deadline.missed ? <FiAlertTriangle /> : <FiClock />}
                {translate(deadline.missed ? "deadlineStatus.missed" : "deadlineStatus.upcoming")}
              </Badge>
              <Time datetime={deadline.deadline_time} fontSize="xs" />
            </HStack>
            <Link to={`/dags/${deadline.dag_id}`}>
              <Text _hover={{ textDecoration: "underline" }} color="fg.info" fontSize="sm" fontWeight="bold">
                {deadline.dag_id}
              </Text>
            </Link>
            <Link to={`/dags/${deadline.dag_id}/runs/${deadline.dag_run_id}`}>
              <Text _hover={{ textDecoration: "underline" }} color="fg.muted" fontSize="xs">
                {deadline.dag_run_id}
              </Text>
            </Link>
          </VStack>
        </Flex>
      ))}
    </VStack>
  );
};

export const Deadlines = () => {
  const { t: translate } = useTranslation("dashboard");
  const refetchInterval = useAutoRefresh({ checkPendingRuns: true });
  const [filters, setFilters] = useState(buildDeadlineFilters);

  useEffect(() => {
    if (refetchInterval === false) {
      return undefined;
    }
    const intervalId = globalThis.setInterval(() => {
      setFilters(buildDeadlineFilters());
    }, refetchInterval);

    return () => {
      globalThis.clearInterval(intervalId);
    };
  }, [refetchInterval]);

  const {
    data: pendingData,
    error: pendingError,
    isLoading: isPendingLoading,
  } = useDeadlinesServiceGetDeadlines(
    {
      dagId: "~",
      dagRunId: "~",
      deadlineTimeGte: filters.pendingFrom,
      limit: LIMIT,
      missed: false,
      orderBy: ["deadline_time"],
    },
    undefined,
    { refetchInterval },
  );
  const {
    data: missedData,
    error: missedError,
    isLoading: isMissedLoading,
  } = useDeadlinesServiceGetDeadlines(
    {
      dagId: "~",
      dagRunId: "~",
      lastUpdatedAtGte: filters.missedSince,
      limit: LIMIT,
      missed: true,
      orderBy: ["-last_updated_at"],
    },
    undefined,
    { refetchInterval },
  );

  return (
    <Box display="flex" flexDirection={{ base: "column", md: "row" }} gap={{ base: 4, md: 8 }}>
      <Box flex={1}>
        <Flex alignItems="center" color="fg.muted" mb={2}>
          <FiClock />
          <Heading ml={1} size="xs">
            {translate("deadlines.upcoming")}
          </Heading>
        </Flex>
        <ErrorAlert error={pendingError} />
        <Box borderRadius="lg" borderWidth={1} overflow="hidden" p={3}>
          <DeadlineList
            deadlines={pendingData?.deadlines ?? []}
            emptyText={translate("deadlines.noUpcoming")}
            isLoading={isPendingLoading}
          />
        </Box>
      </Box>
      <Box flex={1}>
        <Flex alignItems="center" color="fg.muted" mb={2}>
          <FiAlertTriangle />
          <Heading ml={1} size="xs">
            {translate("deadlines.recentlyMissed")}
          </Heading>
        </Flex>
        <ErrorAlert error={missedError} />
        <Box borderRadius="lg" borderWidth={1} overflow="hidden" p={3}>
          <DeadlineList
            deadlines={missedData?.deadlines ?? []}
            emptyText={translate("deadlines.noMissed")}
            isLoading={isMissedLoading}
          />
        </Box>
      </Box>
    </Box>
  );
};
