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
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { act } from "react";
import { describe, expect, it, vi } from "vitest";

import { Wrapper } from "src/utils/Wrapper";

import { Deadlines } from "./Deadlines";

const translations: Record<string, string> = {
  "deadlines.noMissed": "No deadlines were missed in the last 24 hours.",
  "deadlines.noUpcoming": "No upcoming deadlines.",
  "deadlines.recentlyMissed": "Recently Missed Deadlines",
  "deadlines.upcoming": "Upcoming Deadlines",
  "deadlineStatus.missed": "Missed",
  "deadlineStatus.upcoming": "Upcoming",
};

const translate = (key: string) => translations[key] ?? key;

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    i18n: { dir: () => "ltr" },
    // eslint-disable-next-line id-length
    t: translate,
  }),
}));

vi.mock("src/utils", async () => {
  const actual = await vi.importActual("src/utils");

  return {
    ...actual,
    useAutoRefresh: vi.fn(() => false),
  };
});

vi.mock("openapi/queries", () => ({
  useDeadlinesServiceGetDeadlines: vi.fn((params: { missed?: boolean }) =>
    params.missed
      ? {
          data: {
            deadlines: [
              {
                alert_id: null,
                alert_name: "runtime SLA",
                created_at: "2026-05-23T12:00:00Z",
                dag_id: "example_dag",
                dag_run_id: "scheduled__2026-05-23T10:00:00+00:00",
                deadline_time: "2026-05-23T11:00:00Z",
                id: "missed-id",
                missed: true,
              },
            ],
            total_entries: 1,
          },
          error: null,
          isLoading: false,
        }
      : {
          data: {
            deadlines: [
              {
                alert_id: null,
                alert_name: "runtime SLA",
                created_at: "2026-05-24T12:00:00Z",
                dag_id: "future_dag",
                dag_run_id: "scheduled__2026-05-24T10:00:00+00:00",
                deadline_time: "2026-05-24T11:00:00Z",
                id: "upcoming-id",
                missed: false,
              },
            ],
            total_entries: 1,
          },
          error: null,
          isLoading: false,
        },
  ),
}));

const { useDeadlinesServiceGetDeadlines } = await import("openapi/queries");
const { useAutoRefresh } = await import("src/utils");

describe("Dashboard Deadlines", () => {
  it("renders upcoming and recently missed deadlines with Dag and run links", () => {
    render(<Deadlines />, { wrapper: Wrapper });

    expect(screen.getByText("Upcoming Deadlines")).toBeInTheDocument();
    expect(screen.getByText("Recently Missed Deadlines")).toBeInTheDocument();

    expect(screen.getByRole("link", { name: "future_dag" })).toHaveAttribute("href", "/dags/future_dag");
    expect(screen.getByRole("link", { name: "example_dag" })).toHaveAttribute("href", "/dags/example_dag");
    expect(screen.getByRole("link", { name: "scheduled__2026-05-24T10:00:00+00:00" })).toHaveAttribute(
      "href",
      "/dags/future_dag/runs/scheduled__2026-05-24T10:00:00+00:00",
    );
    expect(screen.getByRole("link", { name: "scheduled__2026-05-23T10:00:00+00:00" })).toHaveAttribute(
      "href",
      "/dags/example_dag/runs/scheduled__2026-05-23T10:00:00+00:00",
    );
  });

  it("renders empty states when no deadlines are returned", () => {
    vi.mocked(useDeadlinesServiceGetDeadlines).mockReturnValue({
      data: { deadlines: [], total_entries: 0 },
      error: null,
      isLoading: false,
    } as ReturnType<typeof useDeadlinesServiceGetDeadlines>);

    render(<Deadlines />, { wrapper: Wrapper });

    expect(screen.getByText("No upcoming deadlines.")).toBeInTheDocument();
    expect(screen.getByText("No deadlines were missed in the last 24 hours.")).toBeInTheDocument();
  });

  it("refreshes the deadline filters over time", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-05-23T12:00:00Z"));
    vi.mocked(useAutoRefresh).mockReturnValue(1000);
    vi.mocked(useDeadlinesServiceGetDeadlines).mockReturnValue({
      data: { deadlines: [], total_entries: 0 },
      error: null,
      isLoading: false,
    } as ReturnType<typeof useDeadlinesServiceGetDeadlines>);

    render(<Deadlines />, { wrapper: Wrapper });

    const firstUpcomingCall = vi.mocked(useDeadlinesServiceGetDeadlines).mock.calls[0]?.[0];
    const firstMissedCall = vi.mocked(useDeadlinesServiceGetDeadlines).mock.calls[1]?.[0];

    vi.setSystemTime(new Date("2026-05-23T12:01:00Z"));
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    const laterUpcomingCall = vi.mocked(useDeadlinesServiceGetDeadlines).mock.calls.at(-2)?.[0];
    const laterMissedCall = vi.mocked(useDeadlinesServiceGetDeadlines).mock.calls.at(-1)?.[0];

    expect(firstUpcomingCall?.deadlineTimeGte).not.toBe(laterUpcomingCall?.deadlineTimeGte);
    expect(firstMissedCall?.lastUpdatedAtGte).not.toBe(laterMissedCall?.lastUpdatedAtGte);

    vi.useRealTimers();
  });
});
