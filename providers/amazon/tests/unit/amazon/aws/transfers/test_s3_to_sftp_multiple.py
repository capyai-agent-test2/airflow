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

from unittest import mock

from airflow.providers.amazon.aws.transfers.s3_to_sftp import S3ToSFTPOperator

TASK_ID = "test_s3_to_sftp_multiple"
BUCKET = "test-s3-bucket"
S3_PREFIX = "test/"
SFTP_PATH = "/tmp"


class TestS3ToSFTPOperatorMultipleFiles:
    @mock.patch.object(S3ToSFTPOperator, "_copy_single_file")
    @mock.patch("airflow.providers.amazon.aws.hooks.s3.S3Hook.get_conn")
    @mock.patch("airflow.providers.ssh.hooks.ssh.SSHHook.get_conn")
    def test_execute_multiple_files_same_names(
        self, mock_ssh_hook_get_conn, mock_s3_hook_get_conn, mock_copy_single_file
    ):
        operator = S3ToSFTPOperator(
            task_id=TASK_ID,
            s3_bucket=BUCKET,
            s3_key=S3_PREFIX,
            s3_filenames=["test1.txt", "nested/test2.txt"],
            sftp_path=SFTP_PATH,
        )

        operator.execute(None)

        s3_client = mock_s3_hook_get_conn.return_value
        sftp_client = mock_ssh_hook_get_conn.return_value.open_sftp.return_value
        assert mock_copy_single_file.call_args_list == [
            mock.call(
                s3_client=s3_client,
                sftp_client=sftp_client,
                s3_key="test/test1.txt",
                sftp_path="/tmp/test1.txt",
            ),
            mock.call(
                s3_client=s3_client,
                sftp_client=sftp_client,
                s3_key="test/nested/test2.txt",
                sftp_path="/tmp/nested/test2.txt",
            ),
        ]

    @mock.patch.object(S3ToSFTPOperator, "_copy_single_file")
    @mock.patch("airflow.providers.amazon.aws.hooks.s3.S3Hook.list_keys")
    @mock.patch("airflow.providers.amazon.aws.hooks.s3.S3Hook.get_conn")
    @mock.patch("airflow.providers.ssh.hooks.ssh.SSHHook.get_conn")
    def test_execute_multiple_files_with_prefix_rename(
        self,
        mock_ssh_hook_get_conn,
        mock_s3_hook_get_conn,
        mock_s3_hook_list_keys,
        mock_copy_single_file,
    ):
        mock_s3_hook_list_keys.return_value = ["test/file_a.csv", "test/file_b.csv", "test/other.csv"]
        operator = S3ToSFTPOperator(
            task_id=TASK_ID,
            s3_bucket=BUCKET,
            s3_key=S3_PREFIX,
            s3_filenames="file_",
            sftp_filenames="renamed_",
            sftp_path=SFTP_PATH,
        )

        operator.execute(None)

        mock_s3_hook_list_keys.assert_called_once_with(bucket_name=BUCKET, prefix=S3_PREFIX)
        s3_client = mock_s3_hook_get_conn.return_value
        sftp_client = mock_ssh_hook_get_conn.return_value.open_sftp.return_value
        assert mock_copy_single_file.call_args_list == [
            mock.call(
                s3_client=s3_client,
                sftp_client=sftp_client,
                s3_key="test/file_a.csv",
                sftp_path="/tmp/renamed_a.csv",
            ),
            mock.call(
                s3_client=s3_client,
                sftp_client=sftp_client,
                s3_key="test/file_b.csv",
                sftp_path="/tmp/renamed_b.csv",
            ),
        ]

    @mock.patch.object(S3ToSFTPOperator, "_copy_single_file")
    @mock.patch("airflow.providers.amazon.aws.hooks.s3.S3Hook.list_keys")
    @mock.patch("airflow.providers.amazon.aws.hooks.s3.S3Hook.get_conn")
    @mock.patch("airflow.providers.ssh.hooks.ssh.SSHHook.get_conn")
    def test_execute_multiple_files_with_prefix_filters_prefix_only_and_keeps_destination_path(
        self,
        mock_ssh_hook_get_conn,
        mock_s3_hook_get_conn,
        mock_s3_hook_list_keys,
        mock_copy_single_file,
    ):
        mock_s3_hook_list_keys.return_value = [
            "test/file_a.csv",
            "test/subdir/file_b.csv",
            "test/notfile.csv",
        ]
        operator = S3ToSFTPOperator(
            task_id=TASK_ID,
            s3_bucket=BUCKET,
            s3_key="test",
            s3_filenames="file_",
            sftp_path=SFTP_PATH,
        )

        operator.execute(None)

        s3_client = mock_s3_hook_get_conn.return_value
        sftp_client = mock_ssh_hook_get_conn.return_value.open_sftp.return_value
        assert mock_copy_single_file.call_args_list == [
            mock.call(
                s3_client=s3_client,
                sftp_client=sftp_client,
                s3_key="test/file_a.csv",
                sftp_path="/tmp/file_a.csv",
            )
        ]
