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

Kubernetes RBAC
===============

The ``cncf.kubernetes`` provider uses the Kubernetes API from Airflow components such as the scheduler,
API server, and triggerer. The service account used by those Airflow components must have permission to
manage the Kubernetes resources used by the selected operator or executor.

These permissions apply to the Airflow component talking to the Kubernetes API. Any pod started by an
operator can still use its own ``serviceAccountName`` and may need additional workload-specific permissions.

If you run Airflow in one namespace, bind these rules with a ``Role`` and ``RoleBinding``. If you enable
multi-namespace mode, use a ``ClusterRole`` and ``ClusterRoleBinding`` instead.

Operators
---------

.. list-table::
   :header-rows: 1
   :widths: 30 35 20 15

   * - Operator
     - Resources
     - Verbs
     - Notes
   * - ``KubernetesPodOperator``
     - ``pods``, ``pods/log``, ``pods/exec``, ``events``
     - ``create``, ``get``, ``list``, ``watch``, ``patch``, ``delete``
     - ``pods/exec`` is used for XCom sidecars. ``events`` are used for startup and deferrable event streaming.
   * - ``SparkKubernetesOperator``
     - ``pods``, ``pods/log``, ``events``, ``sparkapplications``, ``sparkapplications/status``
     - ``create``, ``get``, ``list``, ``watch``, ``patch``, ``delete``
     - In addition to pod access, Airflow must manage the SparkApplication custom resource created by the Spark operator.
   * - ``KubernetesJobOperator``
     - ``jobs``, ``jobs/status``, ``pods``, ``pods/log``, ``pods/exec``, ``events``
     - ``create``, ``get``, ``list``, ``watch``, ``patch``, ``delete``
     - ``pods*`` and ``events`` are needed for full functionality such as waiting for pods, streaming logs, and XCom.
   * - ``KubernetesDeleteJobOperator``
     - ``jobs``, ``jobs/status``
     - ``get``, ``watch``, ``delete``
     - ``jobs/status`` is needed when ``delete_on_status`` or ``wait_for_completion`` is used.
   * - ``KubernetesPatchJobOperator``
     - ``jobs``
     - ``get``, ``patch``
     - Patches an existing Job object.
   * - ``KubernetesInstallKueueOperator``
     - Resources from the Kueue release manifest
     - Varies by manifest
     - This operator applies the upstream Kueue installation manifest. In practice, it usually needs cluster-admin level access, so many deployments install Kueue outside Airflow instead.
   * - ``KubernetesStartKueueJobOperator``
     - Same resources as ``KubernetesJobOperator``
     - Same verbs as ``KubernetesJobOperator``
     - Kueue-specific queue selection is implemented with labels and annotations on the Job.

Executors
---------

.. list-table::
   :header-rows: 1
   :widths: 35 35 20 10

   * - Executor
     - Resources
     - Verbs
     - Notes
   * - ``KubernetesExecutor``
     - ``pods``, ``pods/log``
     - ``create``, ``get``, ``list``, ``watch``, ``patch``, ``delete``
     - Matches the executor code path. The Helm chart's pod launcher role also includes ``events`` for broader pod-launching workflows.
   * - ``LocalKubernetesExecutor``
     - Same resources as ``KubernetesExecutor``
     - Same verbs as ``KubernetesExecutor``
     - Only tasks routed to the Kubernetes side need these permissions.

Example role for pod-based workloads
------------------------------------

This example covers ``KubernetesPodOperator`` and the pod-management part of ``KubernetesExecutor``:

.. code-block:: yaml

    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: airflow-pod-launcher
    rules:
      - apiGroups: [""]
        resources: ["pods"]
        verbs: ["create", "get", "list", "watch", "patch", "delete"]
      - apiGroups: [""]
        resources: ["pods/log"]
        verbs: ["get"]
      - apiGroups: [""]
        resources: ["pods/exec"]
        verbs: ["create", "get"]
      - apiGroups: [""]
        resources: ["events"]
        verbs: ["list", "watch"]

Example role for job-based workloads
------------------------------------

This example covers job management. Combine it with the pod-based role when you need log streaming,
pod discovery, or XCom from ``KubernetesJobOperator``:

.. code-block:: yaml

    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: airflow-job-launcher
    rules:
      - apiGroups: ["batch"]
        resources: ["jobs"]
        verbs: ["create", "get", "list", "watch", "patch", "delete"]
      - apiGroups: ["batch"]
        resources: ["jobs/status"]
        verbs: ["get", "watch"]

Example role for Spark applications
-----------------------------------

``SparkKubernetesOperator`` also needs permission to manage the SparkApplication custom resource:

.. code-block:: yaml

    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: airflow-sparkapplication-launcher
    rules:
      - apiGroups: ["sparkoperator.k8s.io"]
        resources: ["sparkapplications"]
        verbs: ["create", "get", "list", "watch", "delete"]
      - apiGroups: ["sparkoperator.k8s.io"]
        resources: ["sparkapplications/status"]
        verbs: ["get"]
