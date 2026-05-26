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
import { useMemo } from "react";
import { useMatch, useNavigate, useSearchParams } from "react-router-dom";

import TriggerDAGModal from "./TriggerDAGModal";
import { getTriggerDagPrefillConfig } from "./urlParams";

type TriggerDagRouteModalProps = {
  readonly dagDisplayName: string;
  readonly dagId: string;
  readonly isPaused: boolean;
};

export const TriggerDagRouteModal = ({ dagDisplayName, dagId, isPaused }: TriggerDagRouteModalProps) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isOpen = useMatch("/dags/:dagId/trigger") !== null;
  const prefillConfig = useMemo(() => getTriggerDagPrefillConfig(searchParams), [searchParams]);

  if (!isOpen) {
    return undefined;
  }

  return (
    <TriggerDAGModal
      dagDisplayName={dagDisplayName}
      dagId={dagId}
      isPaused={isPaused}
      onClose={() => void navigate("..", { relative: "path" })}
      open
      prefillConfig={prefillConfig}
    />
  );
};
