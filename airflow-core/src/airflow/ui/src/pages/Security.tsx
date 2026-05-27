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
import { Box } from "@chakra-ui/react";
import { useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { useAuthLinksServiceGetAuthMenus } from "openapi/queries";
import { ProgressBar } from "src/components/ui";

import { ErrorPage } from "./Error";

// The following iframe sandbox setting is intentionally less restrictive.
// This is considered safe because the framed content originates from the Auth manager,
// which is part of the deployment of Airflow and trusted as per our security policy.
// https://airflow.apache.org/docs/apache-airflow/stable/security/security_model.html
const SANDBOX = "allow-scripts allow-same-origin allow-forms";

const normalizePath = (path: string) => path.replace(/\/+$/u, "");

const extractSecurityLinkPrefix = (href: string) =>
  normalizePath(new URL(href, document.baseURI).pathname).replace(/\/[^/]+$/u, "");

const buildSecurityIframeSrc = (href: string, detailPath: string | undefined) =>
  detailPath === undefined ? href : `${extractSecurityLinkPrefix(href)}/${detailPath}`;

const extractSecurityDetailPath = (iframePath: string, href: string) => {
  const normalizedIframePath = normalizePath(iframePath);
  const linkPrefix = extractSecurityLinkPrefix(href);

  if (normalizedIframePath !== linkPrefix && !normalizedIframePath.startsWith(`${linkPrefix}/`)) {
    return undefined;
  }

  const iframeDetailPath = normalizedIframePath.slice(linkPrefix.length);

  return iframeDetailPath.replace(/^\//u, "");
};

export const Security = () => {
  const { "*": detailPath, page } = useParams();
  const location = useLocation();

  const { data: authLinks, isLoading } = useAuthLinksServiceGetAuthMenus();

  const link = authLinks?.extra_menu_items.find((mi) => mi.text.toLowerCase().replace(" ", "-") === page);

  const navigate = useNavigate();
  // Track when we are already redirecting so that setting iframe.src = "about:blank"
  // (which fires another onLoad event) does not trigger a second navigate call.
  const isRedirecting = useRef(false);

  const onLoad = () => {
    if (isRedirecting.current || link === undefined) {
      return;
    }

    const iframe: HTMLIFrameElement | null = document.querySelector("#security-iframe");

    if (iframe?.contentWindow) {
      const base = new URL(document.baseURI).pathname.replace(/\/$/u, ""); // Remove trailing slash if exists

      if (!iframe.contentWindow.location.pathname.startsWith(`${base}/auth/`)) {
        // Clear the iframe immediately so that the React app does not render its own
        // navigation sidebar inside the iframe, which would produce a duplicate nav bar.
        isRedirecting.current = true;
        iframe.src = "about:blank";
        void navigate("/", { replace: true });

        return;
      }

      const nextDetailPath = extractSecurityDetailPath(iframe.contentWindow.location.pathname, link.href);

      if (nextDetailPath === undefined) {
        return;
      }

      const nextPathname =
        nextDetailPath === "" ? `/security/${page ?? ""}` : `/security/${page ?? ""}/${nextDetailPath}`;
      const nextUrl = `${nextPathname}${iframe.contentWindow.location.search}${iframe.contentWindow.location.hash}`;

      if (nextUrl !== `${location.pathname}${location.search}${location.hash}`) {
        void navigate(nextUrl, { replace: true });
      }
    }
  };

  if (!link) {
    if (isLoading) {
      return (
        <Box flexGrow={1}>
          <ProgressBar />
        </Box>
      );
    }

    return <ErrorPage />;
  }

  return (
    <Box flexGrow={1} m={-3}>
      {
        // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
        <iframe
          id="security-iframe"
          onLoad={onLoad}
          sandbox={SANDBOX}
          src={buildSecurityIframeSrc(link.href, detailPath)}
          style={{ height: "100%", width: "100%" }}
          title={link.text}
        />
      }
    </Box>
  );
};
