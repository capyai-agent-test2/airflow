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
import { Box, Flex, HStack, Separator, Stack, Table, Text } from "@chakra-ui/react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type {
  AssetEventResponse,
  DagRunAssetReference,
  DagRunState,
  QueuedEventCollectionResponse,
} from "openapi/requests/types.gen";
import RenderedJsonField from "src/components/RenderedJsonField";
import { StateBadge } from "src/components/StateBadge";
import Time from "src/components/Time";
import { RouterLink } from "src/components/ui";

const pendingDagRunStates = new Set(["deferred", "planned", "queued", "running"]);

const sourceLabelFromExtra = (event: AssetEventResponse): string | undefined => {
  const fromRestAPI = event.extra?.from_rest_api;
  const fromTrigger = event.extra?.from_trigger;

  if (fromRestAPI === true) {
    return "API";
  }
  if (fromTrigger === true) {
    return "Trigger";
  }

  return undefined;
};

const filterQueuedEvents = (event: AssetEventResponse, queuedEvents?: QueuedEventCollectionResponse) =>
  (queuedEvents?.queued_events ?? []).filter((queuedEvent) => queuedEvent.created_at >= event.timestamp);

const isActiveEvent = (dagRuns: Array<DagRunAssetReference>, queuedEventCount: number) =>
  queuedEventCount > 0 || dagRuns.some((dagRun) => pendingDagRunStates.has(dagRun.state));

export const AssetEventDetails = ({
  event,
  queuedEvents,
}: {
  readonly event?: AssetEventResponse;
  readonly queuedEvents?: QueuedEventCollectionResponse;
}) => {
  const { t: translate } = useTranslation(["assets", "common", "dashboard"]);

  const currentQueuedEvents = useMemo(
    () => (event === undefined ? [] : filterQueuedEvents(event, queuedEvents)),
    [event, queuedEvents],
  );

  if (event === undefined) {
    return undefined;
  }

  const sourceLabel = sourceLabelFromExtra(event);
  const active = isActiveEvent(event.created_dagruns, currentQueuedEvents.length);
  const eventExtra = event.extra ?? undefined;

  return (
    <Box borderRadius={8} borderWidth={1} data-testid="asset-event-details" mb={3} p={4}>
      <Flex alignItems="center" justifyContent="space-between" mb={3}>
        <Stack gap={0}>
          <Text fontSize="sm" fontWeight="medium">
            {translate("common:assetEvent_one")}
          </Text>
          <Text fontSize="lg" fontWeight="bold">
            <Time datetime={event.timestamp} />
          </Text>
        </Stack>
        {active ? (
          <HStack>
            <StateBadge state="running" />
            <Text>{translate("common:states.running")}</Text>
          </HStack>
        ) : undefined}
      </Flex>
      <Table.Root size="sm" striped>
        <Table.Body>
          <Table.Row>
            <Table.Cell>{translate("dashboard:source")}</Table.Cell>
            <Table.Cell>
              {sourceLabel ?? (
                <RouterLink
                  to={`/dags/${event.source_dag_id}/runs/${event.source_run_id}/tasks/${event.source_task_id}${event.source_map_index > -1 ? `/mapped/${event.source_map_index}` : ""}`}
                >
                  {event.source_dag_id}
                </RouterLink>
              )}
            </Table.Cell>
          </Table.Row>
          {event.partition_key === undefined ? undefined : (
            <Table.Row>
              <Table.Cell>{translate("common:dagRun.partitionKey")}</Table.Cell>
              <Table.Cell>{event.partition_key}</Table.Cell>
            </Table.Row>
          )}
        </Table.Body>
      </Table.Root>
      {event.created_dagruns.length > 0 ? (
        <>
          <Separator my={3} />
          <Stack gap={2}>
            <Text fontWeight="medium">
              {translate("common:dagRun_other", { count: event.created_dagruns.length })}
            </Text>
            {event.created_dagruns.map((dagRun) => (
              <Flex gap={2} key={`${dagRun.dag_id}-${dagRun.run_id}`} wrap="wrap">
                <StateBadge state={dagRun.state as DagRunState} />
                <RouterLink to={`/dags/${dagRun.dag_id}/runs/${dagRun.run_id}`}>{dagRun.dag_id}</RouterLink>
                <Text color="fg.muted">{dagRun.run_id}</Text>
              </Flex>
            ))}
          </Stack>
        </>
      ) : undefined}
      {currentQueuedEvents.length > 0 ? (
        <>
          <Separator my={3} />
          <Stack gap={2}>
            <Text fontWeight="medium">
              {translate("common:pendingDagRun_other", { count: currentQueuedEvents.length })}
            </Text>
            {currentQueuedEvents.map((queuedEvent) => (
              <Flex
                gap={2}
                key={`${queuedEvent.asset_id}-${queuedEvent.dag_id}-${queuedEvent.created_at}`}
                wrap="wrap"
              >
                <StateBadge state="queued" />
                <RouterLink to={`/dags/${queuedEvent.dag_id}`}>{queuedEvent.dag_display_name}</RouterLink>
                <Text color="fg.muted">
                  <Time datetime={queuedEvent.created_at} />
                </Text>
              </Flex>
            ))}
          </Stack>
        </>
      ) : undefined}
      {eventExtra === undefined || Object.keys(eventExtra).length === 0 ? undefined : (
        <>
          <Separator my={3} />
          <Stack gap={2}>
            <Text fontWeight="medium">{translate("assets:additional_data")}</Text>
            <RenderedJsonField collapsed content={eventExtra} />
          </Stack>
        </>
      )}
    </Box>
  );
};
