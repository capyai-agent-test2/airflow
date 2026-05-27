#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from collections.abc import Iterable

from airflow.models.taskinstance import PAST_DEPENDS_MET
from airflow.ti_deps.deps.base_ti_dep import BaseTIDep

# The following constants are taken from the SkipMixin class in the standard provider
# The key used by SkipMixin to store XCom data.
XCOM_SKIPMIXIN_KEY = "skipmixin_key"

# The dictionary key used to denote task IDs that are skipped
XCOM_SKIPMIXIN_SKIPPED = "skipped"

# The dictionary key used to denote task IDs that are followed
XCOM_SKIPMIXIN_FOLLOWED = "followed"


class NotPreviouslySkippedDep(BaseTIDep):
    """
    Determine if this task should be skipped.

    Based on any of the task's direct upstream relatives have decided this task should
    be skipped.
    """

    NAME = "Not Previously Skipped"
    IGNORABLE = True
    IS_TASK_DEP = True

    def _get_dep_statuses(self, ti, session, dep_context):
        from airflow.exceptions import NotMapped
        from airflow.models.expandinput import NotFullyPopulated
        from airflow.serialization.definitions.mappedoperator import get_mapped_ti_count
        from airflow.utils.state import TaskInstanceState

        upstream = ti.task.get_direct_relatives(upstream=True)

        finished_tis = dep_context.ensure_finished_tis(ti.get_dagrun(session), session)

        finished_task_ids = {t.task_id for t in finished_tis}

        for parent in upstream:
            if parent.inherits_from_skipmixin:
                if parent.task_id not in finished_task_ids:
                    # This can happen if the parent task has not yet run.
                    continue

                # Use the map indexes relevant to this task instance when the parent and
                # child share a mapped task group. Otherwise fall back to the parent's own
                # map context, where unmapped parents write XCom with map_index=-1.
                try:
                    expanded_ti_count = get_mapped_ti_count(ti.task, ti.run_id, session=session)
                except (NotFullyPopulated, NotMapped):
                    expanded_ti_count = None

                if expanded_ti_count is None:
                    xcom_map_index = ti.map_index if parent.is_mapped else -1
                else:
                    relevant_map_indexes = ti.get_relevant_upstream_map_indexes(
                        upstream=parent,
                        ti_count=expanded_ti_count,
                        session=session,
                    )
                    xcom_map_index = relevant_map_indexes if relevant_map_indexes is not None else -1
                prev_result = ti.xcom_pull(
                    task_ids=parent.task_id,
                    key=XCOM_SKIPMIXIN_KEY,
                    session=session,
                    map_indexes=xcom_map_index,
                )

                if prev_result is None:
                    # This can happen if the parent task has not yet run.
                    continue

                if isinstance(prev_result, Iterable) and not isinstance(prev_result, dict):
                    prev_results = prev_result
                else:
                    prev_results = (prev_result,)

                should_skip = False
                for prev_result_item in prev_results:
                    if prev_result_item is None:
                        continue
                    if (
                        XCOM_SKIPMIXIN_FOLLOWED in prev_result_item
                        and ti.task_id not in prev_result_item[XCOM_SKIPMIXIN_FOLLOWED]
                    ):
                        # Skip any tasks that are not in "followed"
                        should_skip = True
                    elif (
                        XCOM_SKIPMIXIN_SKIPPED in prev_result_item
                        and ti.task_id in prev_result_item[XCOM_SKIPMIXIN_SKIPPED]
                    ):
                        # Skip any tasks that are in "skipped"
                        should_skip = True
                    if should_skip:
                        break

                if should_skip:
                    # If the parent SkipMixin has run, and the XCom result stored indicates this
                    # ti should be skipped, set ti.state to SKIPPED and fail the rule so that the
                    # ti does not execute.
                    if dep_context.wait_for_past_depends_before_skipping:
                        past_depends_met = ti.xcom_pull(
                            task_ids=ti.task_id, key=PAST_DEPENDS_MET, session=session, default=False
                        )
                        if not past_depends_met:
                            yield self._failing_status(
                                reason="Task should be skipped but the past depends are not met"
                            )
                            return
                    ti.set_state(TaskInstanceState.SKIPPED, session)
                    yield self._failing_status(
                        reason=f"Skipping because of previous XCom result from parent task {parent.task_id}"
                    )
                    return
