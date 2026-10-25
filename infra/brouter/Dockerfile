# BRouter routing server (ADR-0004). The official release ZIP is fetched on the host by
# fetch-release.sh into the git-ignored .cache/ directory (the container build cannot reach GitHub
# behind TLS-intercepting networks). The ZIP is pinned by version and SHA-256 and verified again here.
FROM eclipse-temurin:21-jdk AS build
ARG BROUTER_VERSION=1.7.10
ARG BROUTER_ZIP_SHA256=023fec3ba997758e8cd7ab9e1bae52e962af3f00b57683e3de86b84ffad01532
COPY .cache/brouter-${BROUTER_VERSION}.zip /tmp/brouter.zip
RUN echo "${BROUTER_ZIP_SHA256}  /tmp/brouter.zip" | sha256sum -c - \
 && cd /tmp \
 && jar xf brouter.zip "brouter-${BROUTER_VERSION}/brouter-${BROUTER_VERSION}-all.jar" \
 && mkdir -p /opt/brouter \
 && mv "/tmp/brouter-${BROUTER_VERSION}/brouter-${BROUTER_VERSION}-all.jar" /opt/brouter/brouter.jar

FROM eclipse-temurin:21-jre
COPY --from=build /opt/brouter/brouter.jar /opt/brouter/brouter.jar
COPY entrypoint.sh /usr/local/bin/brouter-entrypoint
RUN chmod 0755 /usr/local/bin/brouter-entrypoint
EXPOSE 17777
ENTRYPOINT ["/usr/local/bin/brouter-entrypoint"]
