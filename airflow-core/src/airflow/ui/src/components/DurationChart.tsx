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
import { Box, Heading, useToken } from "@chakra-ui/react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Legend,
  Tooltip,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import dayjs from "dayjs";
import { Bar } from "react-chartjs-2";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import type { TaskInstanceResponse, GridRunsResponse } from "openapi/requests/types.gen";
import { useTimezone } from "src/context/timezone";
import { getComputedCSSVariableValue } from "src/theme";
import { DEFAULT_DATETIME_FORMAT, formatDate, renderDuration } from "src/utils/datetimeUtils";
import { buildTaskInstanceUrl } from "src/utils/links";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  BarElement,
  LineElement,
  Filler,
  Legend,
  Tooltip,
  annotationPlugin,
);

const durationUnits = {
  hours: { suffix: "h", value: 60 * 60 },
  minutes: { suffix: "m", value: 60 },
  seconds: { suffix: "s", value: 1 },
} as const;

const getDurationUnit = (maxDuration: number) => {
  if (maxDuration >= durationUnits.hours.value) {
    return durationUnits.hours;
  }

  if (maxDuration >= durationUnits.minutes.value) {
    return durationUnits.minutes;
  }

  return durationUnits.seconds;
};

const formatDurationByUnit = (duration: number, unit: (typeof durationUnits)[keyof typeof durationUnits]) => {
  const value = duration / unit.value;

  return `${Number.isInteger(value) ? value : value.toFixed(1)}${unit.suffix}`;
};

const getMedian = (values: Array<number>) => {
  if (values.length === 0) {
    return 0;
  }

  const sortedValues = [...values].sort((left, right) => left - right);
  const middleIndex = Math.floor(sortedValues.length / 2);

  if (sortedValues.length % 2 === 1) {
    return sortedValues[middleIndex] ?? 0;
  }

  return ((sortedValues[middleIndex - 1] ?? 0) + (sortedValues[middleIndex] ?? 0)) / 2;
};

type RunResponse = GridRunsResponse | TaskInstanceResponse;

const getDuration = (start: string, end: string | null) => {
  const startDate = dayjs(start);
  const endDate = end === null ? dayjs() : dayjs(end);

  if (!startDate.isValid() || !endDate.isValid()) {
    return 0;
  }

  return dayjs.duration(endDate.diff(startDate)).asSeconds();
};

const getTickLabelFormat = (entries: Array<RunResponse>): string => {
  if (entries.length < 2) {
    return "HH:mm:ss";
  }

  const first = dayjs(entries[0]?.run_after);
  const last = dayjs(entries[entries.length - 1]?.run_after);

  if (!first.isValid() || !last.isValid()) {
    return "MMM DD";
  }

  const diffInDays = Math.abs(last.diff(first, "day"));

  return diffInDays < 1 ? "HH:mm:ss" : "MMM DD HH:mm";
};

export const DurationChart = ({
  entries,
  isAutoRefreshing = false,
  kind,
}: {
  readonly entries: Array<RunResponse> | undefined;
  readonly isAutoRefreshing?: boolean;
  readonly kind: "Dag Run" | "Task Instance";
}) => {
  const { t: translate } = useTranslation(["components", "common"]);
  const navigate = useNavigate();
  const { selectedTimezone } = useTimezone();
  const [queuedColorToken] = useToken("colors", ["queued.solid"]);

  // Get states and create color tokens for them
  const states = entries?.map((entry) => entry.state).filter(Boolean) ?? [];
  const stateColorTokens = useToken(
    "colors",
    states.map((state) => `${state}.solid`),
  );

  if (!entries) {
    return undefined;
  }

  // Create a mapping of state to color for easy lookup
  const stateColorMap: Record<string, string> = {};

  states.forEach((state, index) => {
    if (state) {
      stateColorMap[state] = getComputedCSSVariableValue(stateColorTokens[index] ?? "oklch(0.5 0 0)");
    }
  });

  const queuedDurations = entries.map((entry: RunResponse) => {
    switch (kind) {
      case "Dag Run": {
        const run = entry as GridRunsResponse;

        return run.queued_at !== null && run.start_date !== null && run.queued_at < run.start_date
          ? Number(getDuration(run.queued_at, run.start_date))
          : 0;
      }
      case "Task Instance": {
        const taskInstance = entry as TaskInstanceResponse;

        return taskInstance.queued_when !== null &&
          taskInstance.start_date !== null &&
          taskInstance.queued_when < taskInstance.start_date
          ? Number(getDuration(taskInstance.queued_when, taskInstance.start_date))
          : 0;
      }
      default:
        return 0;
    }
  });
  const runDurations = entries.map((entry: RunResponse) =>
    entry.start_date === null ? 0 : Number(getDuration(entry.start_date, entry.end_date)),
  );
  const totalDurations = queuedDurations.map((duration, index) => duration + (runDurations[index] ?? 0));
  const medianTotalDuration = getMedian(totalDurations);
  const durationUnit = getDurationUnit(Math.max(...totalDurations, 0));

  const medianAnnotation = {
    borderColor: "#3182ce",
    borderDash: [6, 6],
    borderWidth: 2,
    label: {
      backgroundColor: "#3182ce",
      content: renderDuration(medianTotalDuration, false) ?? "0",
      display: medianTotalDuration > 0,
      position: "end" as const,
    },
    scaleID: "y",
    value: medianTotalDuration,
  };

  return (
    <Box>
      <Heading pb={2} size="sm" textAlign="center">
        {kind === "Dag Run"
          ? translate("durationChart.lastDagRun", { count: entries.length })
          : translate("durationChart.lastTaskInstance", { count: entries.length })}
      </Heading>
      <Bar
        data={{
          datasets: [
            {
              backgroundColor: getComputedCSSVariableValue(queuedColorToken ?? "oklch(0.5 0 0)"),
              data: queuedDurations,
              label: translate("durationChart.queuedDuration"),
            },
            {
              backgroundColor: entries.map(
                (entry: RunResponse) =>
                  (entry.state ? stateColorMap[entry.state] : undefined) ?? "oklch(0.5 0 0)",
              ),
              data: runDurations,
              label: translate("durationChart.runDuration"),
            },
          ],
          labels: entries.map((entry: RunResponse) => dayjs(entry.run_after).format(DEFAULT_DATETIME_FORMAT)),
        }}
        datasetIdKey="id"
        options={{
          animation: isAutoRefreshing ? false : undefined,
          onClick: (_event, elements) => {
            const [element] = elements;

            if (!element) {
              return;
            }

            switch (kind) {
              case "Dag Run": {
                const entry = entries[element.index] as GridRunsResponse | undefined;
                const baseUrl = `/dags/${entry?.dag_id}/runs/${entry?.run_id}`;

                void Promise.resolve(navigate(baseUrl));
                break;
              }
              case "Task Instance": {
                const entry = entries[element.index] as TaskInstanceResponse | undefined;

                if (entry === undefined) {
                  break;
                }

                const baseUrl = buildTaskInstanceUrl({
                  currentPathname: location.pathname,
                  dagId: entry.dag_id,
                  isMapped: entry.map_index >= 0,
                  mapIndex: entry.map_index.toString(),
                  runId: entry.dag_run_id,
                  taskId: entry.task_id,
                });

                void Promise.resolve(navigate(baseUrl));
                break;
              }
              default:
            }
          },
          onHover: (_event, elements, chart) => {
            chart.canvas.style.cursor = elements.length > 0 ? "pointer" : "default";
          },
          plugins: {
            annotation: {
              annotations: {
                medianAnnotation,
              },
            },
            legend: {
              display: true,
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const datasetLabel = context.dataset.label ?? "";

                  const formatted = renderDuration(context.parsed.y, false) ?? "0";

                  return datasetLabel ? `${datasetLabel}: ${formatted}` : formatted;
                },
              },
            },
          },
          responsive: true,
          scales: {
            x: {
              stacked: true,
              ticks: {
                callback: (_value, index) =>
                  formatDate(entries[index]?.run_after, selectedTimezone, getTickLabelFormat(entries)),
                maxTicksLimit: 3,
              },
              title: { align: "end", display: true, text: translate("common:dagRun.runAfter") },
            },
            y: {
              ticks: {
                callback: (value) => {
                  const num = typeof value === "number" ? value : Number(value);

                  return formatDurationByUnit(num, durationUnit);
                },
              },
              title: { align: "end", display: true, text: translate("common:duration") },
            },
          },
        }}
      />
    </Box>
  );
};
