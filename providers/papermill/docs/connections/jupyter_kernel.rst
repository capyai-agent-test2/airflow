 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.



.. _howto/connection:jupyter_kernel:

Jupyter Kernel Connection
=========================

The Jupyter Kernel connection type enables remote kernel connections.


Default Connection ID
---------------------

  The default Jupyter Kernel connection ID is ``jupyter_kernel_default``.

Configuring the Connection
--------------------------

host
    HOSTNAME/IP of the remote Jupyter Kernel. When using a Jupyter Gateway over HTTP or HTTPS,
    this can also be the full gateway URL.

Extra (optional)
    Specify the extra parameters (as json dictionary) that can be used in kernel connection.
    All parameters are optional.

    * ``session_key``: Session key to initiate a connection to remote kernel [default: ''].
    * ``shell_port``: SHELL port [default: 60316].
    * ``iopub_port``: IOPUB port [default: 60317].
    * ``stdin_port``: STDIN port [default: 60318].
    * ``control_port``: CONTROL port [default: 60319].
    * ``hb_port``: HEARTBEAT port [default: 60320].
    * ``gateway_url``: Optional Jupyter Gateway URL. If omitted, Airflow also treats an
      ``http://`` or ``https://`` value in ``host`` as the gateway URL.
    * ``gateway_ws_url``: Optional websocket URL for the gateway. If omitted, it is derived
      from the gateway URL.
    * ``auth_token``: Optional authentication token sent to the gateway.
    * ``auth_scheme``: Optional authentication scheme prefix for the token, for example
      ``Bearer`` or ``token``.
    * ``validate_cert``: Whether to validate HTTPS certificates [default: true].

password
    Optional authentication token for gateway connections. When set, it takes precedence over
    ``extra.auth_token``.

If you are configuring the connection via a URI, ensure that all components of the URI are URL-encoded.

Examples
--------

**Set Remote Kernel Connection as Environment Variable (URI)**
  .. code-block:: bash

     export AIRFLOW_CONN_JUPYTER_KERNEL_DEFAULT='{"host": "remote_host", "extra": {"session_key": "notebooks"}}'

**Snippet for create Connection as URI**:
  .. code-block:: python

    from airflow.models.connection import Connection

    conn = Connection(
        conn_id="jupyter_kernel_default",
        conn_type="jupyter_kernel",
        host="remote_host",
        extra={
            # Specify extra parameters here
            "session_key": "notebooks",
        },
    )

    # Generate Environment Variable Name
    env_key = f"AIRFLOW_CONN_{conn.conn_id.upper()}"

    print(f"{env_key}='{conn.get_uri()}'")

**Set Gateway Connection as Environment Variable (URI)**
  .. code-block:: bash

     export AIRFLOW_CONN_JUPYTER_KERNEL_DEFAULT='{"host": "https://gateway.example.com", "extra": {"auth_token": "secret-token", "auth_scheme": "Bearer"}}'
