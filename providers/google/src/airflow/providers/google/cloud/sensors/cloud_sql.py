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
"""Sensors for Google Cloud SQL."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from airflow.providers.common.compat.sdk import AirflowException, BaseSensorOperator, conf
from airflow.providers.google.cloud.hooks.cloud_sql import CloudSQLHook
from airflow.providers.google.cloud.triggers.cloud_sql import CloudSQLNoOperationInProgressTrigger
from airflow.providers.google.common.hooks.base_google import PROVIDE_PROJECT_ID

if TYPE_CHECKING:
    from airflow.providers.common.compat.sdk import Context


class CloudSQLNoOperationInProgressSensor(BaseSensorOperator):
    """
    Wait until a Cloud SQL instance has no non-terminal administrative operations.

    :param instance: Cloud SQL instance ID. This does not include the project ID.
    :param project_id: Optional, Google Cloud Project ID. If set to None or missing,
            the default project_id from the Google Cloud connection is used.
    :param gcp_conn_id: The connection ID used to connect to Google Cloud.
    :param impersonation_chain: Optional service account to impersonate using short-term
        credentials, or chained list of accounts required to get the access_token
        of the last account in the list, which will be impersonated in the request.
        If set as a string, the account must grant the originating account
        the Service Account Token Creator IAM role.
        If set as a sequence, the identities from the list must grant
        Service Account Token Creator IAM role to the directly preceding identity, with first
        account from the list granting this role to the originating account (templated).
    :param deferrable: Run sensor in deferrable mode.
    """

    template_fields: Sequence[str] = ("project_id", "instance", "impersonation_chain")
    ui_color = "#D3EDFB"

    def __init__(
        self,
        *,
        instance: str,
        project_id: str = PROVIDE_PROJECT_ID,
        gcp_conn_id: str = "google_cloud_default",
        impersonation_chain: str | Sequence[str] | None = None,
        deferrable: bool = conf.getboolean("operators", "default_deferrable", fallback=False),
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.instance = instance
        self.project_id = project_id
        self.gcp_conn_id = gcp_conn_id
        self.impersonation_chain = impersonation_chain
        self.deferrable = deferrable

    def poke(self, context: Context) -> bool:
        hook = CloudSQLHook(
            gcp_conn_id=self.gcp_conn_id,
            api_version="v1beta4",
            impersonation_chain=self.impersonation_chain,
        )
        return not hook.is_instance_operation_in_progress(project_id=self.project_id, instance=self.instance)

    def execute(self, context: Context) -> None:
        if not self.deferrable:
            return super().execute(context)

        if self.poke(context=context):
            return None

        self.defer(
            timeout=timedelta(seconds=self.timeout),
            trigger=CloudSQLNoOperationInProgressTrigger(
                instance=self.instance,
                project_id=self.project_id,
                gcp_conn_id=self.gcp_conn_id,
                impersonation_chain=self.impersonation_chain,
                poke_interval=self.poke_interval,
            ),
            method_name="execute_complete",
        )

    def execute_complete(self, context: dict[str, Any], event: dict[str, str] | None = None) -> str:
        if event:
            if event["status"] == "success":
                return event["message"]
            raise AirflowException(event["message"])

        raise AirflowException("No event received in trigger callback")
