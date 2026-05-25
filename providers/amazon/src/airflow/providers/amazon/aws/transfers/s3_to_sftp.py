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

from collections.abc import Sequence
from posixpath import join as posixpath_join
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.common.compat.sdk import BaseOperator
from airflow.providers.ssh.hooks.ssh import SSHHook

if TYPE_CHECKING:
    from airflow.sdk import Context


class S3ToSFTPOperator(BaseOperator):
    """
    This operator enables the transferring of files from S3 to a SFTP server.

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:S3ToSFTPOperator`

    :param sftp_conn_id: The sftp connection id. The name or identifier for
        establishing a connection to the SFTP server.
    :param sftp_path: The sftp remote path. For one file it is mandatory to include the file as well.
        For multiple files, it is the path where the files will be uploaded.
    :param sftp_remote_host: The remote host of the SFTP server. Overrides host in
        Connection.
    :param aws_conn_id: The Airflow connection used for AWS credentials.
        If this is None or empty then the default boto3 behaviour is used. If
        running Airflow in a distributed manner and aws_conn_id is None or
        empty, then default boto3 configuration would be used (and must be
        maintained on each worker node).
    :param s3_bucket: The targeted s3 bucket. This is the S3 bucket from
        where the file is downloaded.
    :param s3_key: The targeted s3 key. For one file it must include the file path. For several,
        it must point to the shared prefix.
    :param s3_filenames: Only used if you want to move multiple files. You can pass a list
        with exact filenames present in the S3 prefix, or a prefix that all files must meet. It
        can also be the string '*' for moving all the files within the S3 prefix.
    :param sftp_filenames: Only used if you want to move multiple files and name them different from
        the originals from S3. It can be a list of filenames or file prefix (that will replace
        the S3 prefix).
    :param confirm: specify if the SFTP operation should be confirmed, defaults to True.
        When True, a stat will be performed on the remote file after upload to verify
        the file size matches and confirm successful transfer.
    """

    template_fields: Sequence[str] = ("s3_key", "sftp_path", "s3_bucket", "s3_filenames", "sftp_filenames")

    def __init__(
        self,
        *,
        s3_bucket: str,
        s3_key: str,
        sftp_path: str,
        s3_filenames: str | list[str] | None = None,
        sftp_filenames: str | list[str] | None = None,
        sftp_conn_id: str = "ssh_default",
        sftp_remote_host: str = "",
        aws_conn_id: str | None = "aws_default",
        confirm: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.sftp_conn_id = sftp_conn_id
        self.sftp_path = sftp_path
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.s3_filenames = s3_filenames
        self.sftp_filenames = sftp_filenames
        self.sftp_remote_host = sftp_remote_host
        self.aws_conn_id = aws_conn_id
        self.confirm = confirm

    @staticmethod
    def get_s3_key(s3_key: str) -> str:
        """Parse the correct format for S3 keys regardless of how the S3 url is passed."""
        parsed_s3_key = urlsplit(s3_key)
        return parsed_s3_key.path.lstrip("/")

    def _copy_single_file(self, s3_client, sftp_client, s3_key: str, sftp_path: str) -> None:
        with NamedTemporaryFile("w") as file:
            s3_client.download_file(self.s3_bucket, s3_key, file.name)
            sftp_client.put(file.name, sftp_path, confirm=self.confirm)

    def execute(self, context: Context) -> None:
        self.s3_key = self.get_s3_key(self.s3_key)

        # SSHHook will handle a None/"" sftp_remote_host
        ssh_hook = SSHHook(ssh_conn_id=self.sftp_conn_id, remote_host=self.sftp_remote_host)
        s3_hook = S3Hook(self.aws_conn_id)

        s3_client = s3_hook.get_conn()
        sftp_client = ssh_hook.get_conn().open_sftp()

        if self.s3_filenames:
            if isinstance(self.s3_filenames, str):
                self.log.info("Getting files in %s", self.s3_key)
                files = s3_hook.list_keys(bucket_name=self.s3_bucket, prefix=self.s3_key) or []
                if self.s3_filenames != "*":
                    s3_filename: str = self.s3_filenames
                    files = [
                        file
                        for file in files
                        if file.removeprefix(self.s3_key).lstrip("/").startswith(s3_filename)
                    ]

                for file in files:
                    self.log.info("Moving file %s", file)
                    filename = file.removeprefix(self.s3_key).lstrip("/")
                    if self.sftp_filenames and isinstance(self.sftp_filenames, str):
                        filename = filename.replace(self.s3_filenames, self.sftp_filenames)

                    self._copy_single_file(
                        s3_client=s3_client,
                        sftp_client=sftp_client,
                        s3_key=file,
                        sftp_path=posixpath_join(self.sftp_path, filename),
                    )
            else:
                if self.sftp_filenames and isinstance(self.sftp_filenames, list):
                    for s3_file, sftp_file in zip(self.s3_filenames, self.sftp_filenames):
                        self._copy_single_file(
                            s3_client=s3_client,
                            sftp_client=sftp_client,
                            s3_key=posixpath_join(self.s3_key, s3_file),
                            sftp_path=posixpath_join(self.sftp_path, sftp_file),
                        )
                else:
                    for s3_file in self.s3_filenames:
                        self._copy_single_file(
                            s3_client=s3_client,
                            sftp_client=sftp_client,
                            s3_key=posixpath_join(self.s3_key, s3_file),
                            sftp_path=posixpath_join(self.sftp_path, s3_file),
                        )
            return

        self._copy_single_file(
            s3_client=s3_client,
            sftp_client=sftp_client,
            s3_key=self.s3_key,
            sftp_path=self.sftp_path,
        )
