// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

(() => {
  const selectors = Array.from(document.querySelectorAll(".docs-version-selector"));

  if (selectors.length === 0) {
    return;
  }

  const getPageParts = () => {
    const docsPathMatch = window.location.pathname.match(/^\/docs\/([^/]+)\/([^/]+)\/?(.*)$/);

    if (!docsPathMatch) {
      return null;
    }

    return {
      packageName: docsPathMatch[1],
      version: docsPathMatch[2],
      pagePath: docsPathMatch[3],
    };
  };

  const parseVersion = (version) =>
    version.split(/[.-]/).map((part) => {
      const parsedPart = Number.parseInt(part, 10);

      return Number.isNaN(parsedPart) ? 0 : parsedPart;
    });

  const compareVersions = (left, right) => {
    const leftParts = parseVersion(left);
    const rightParts = parseVersion(right);
    const longestLength = Math.max(leftParts.length, rightParts.length);

    for (let index = 0; index < longestLength; index += 1) {
      const leftPart = leftParts[index] ?? 0;
      const rightPart = rightParts[index] ?? 0;

      if (leftPart !== rightPart) {
        return leftPart - rightPart;
      }
    }

    return left.localeCompare(right);
  };

  const extractMinorVersion = (version) => {
    const [majorVersion, minorVersion] = version.split(".");

    return `${majorVersion}.${minorVersion ?? "0"}`;
  };

  const getLatestPatchVersions = (versions, currentVersion) => {
    const latestPatchVersionsByMinor = new Map();

    [...versions].sort(compareVersions).reverse().forEach((version) => {
      const minorVersion = extractMinorVersion(version);

      if (!latestPatchVersionsByMinor.has(minorVersion)) {
        latestPatchVersionsByMinor.set(minorVersion, version);
      }
    });

    if (
      currentVersion &&
      currentVersion !== "stable" &&
      !Array.from(latestPatchVersionsByMinor.values()).includes(currentVersion)
    ) {
      latestPatchVersionsByMinor.set(currentVersion, currentVersion);
    }

    return Array.from(latestPatchVersionsByMinor.values()).sort(compareVersions).reverse();
  };

  const buildVersionUrl = (packageName, version, pagePath) => {
    const normalizedPagePath = pagePath ? `/${pagePath}` : "/";

    return `/docs/${packageName}/${version}${normalizedPagePath}`;
  };

  const addVersionItem = (menu, item) => {
    const link = document.createElement("a");

    link.className = "dropdown-item";
    link.href = item.href;
    link.textContent = item.label;

    if (item.current) {
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
      link.textContent = `${item.label} (current)`;
    }

    menu.appendChild(link);
  };

  const updateButtonLabel = (selector, currentVersion, stableVersion) => {
    if (currentVersion !== "stable") {
      return;
    }

    const selectedVersion = selector.querySelector(".version");

    if (selectedVersion) {
      selectedVersion.textContent = `Stable (${stableVersion})`;
    }
  };

  fetch("/_gen/packages-metadata.json")
    .then((response) => response.json())
    .then((packagesMetadata) => {
      const pageParts = getPageParts();

      if (!pageParts) {
        return;
      }

      const packageMetadata = packagesMetadata.find(
        (candidatePackage) => candidatePackage["package-name"] === pageParts.packageName,
      );

      if (!packageMetadata) {
        return;
      }

      const stableVersion = packageMetadata["stable-version"];
      const versions = getLatestPatchVersions(packageMetadata["all-versions"], pageParts.version);
      let isRendering = false;

      const renderVersionSelector = (selector) => {
        const menu = selector.querySelector(".dropdown-menu");

        if (!menu) {
          return;
        }

        isRendering = true;
        menu.replaceChildren();

        updateButtonLabel(selector, pageParts.version, stableVersion);
        addVersionItem(menu, {
          href: buildVersionUrl(pageParts.packageName, "stable", pageParts.pagePath),
          label: `Stable (${stableVersion})`,
          current: pageParts.version === "stable",
        });

        versions.forEach((version) => {
          addVersionItem(menu, {
            href: buildVersionUrl(pageParts.packageName, version, pageParts.pagePath),
            label: version,
            current: pageParts.version === version,
          });
        });

        queueMicrotask(() => {
          isRendering = false;
        });
      };

      selectors.forEach((selector) => {
        const menu = selector.querySelector(".dropdown-menu");

        if (!menu) {
          return;
        }

        const observer = new MutationObserver(() => {
          if (!isRendering) {
            renderVersionSelector(selector);
          }
        });

        renderVersionSelector(selector);
        observer.observe(menu, { childList: true });
      });
    })
    .catch(() => {
      // Leave the theme-provided selector unchanged when metadata is unavailable.
    });
})();
