#
# Build gcloud on Alpine Linux.
#
# Usage:
#   $ docker build -t local/gcloud -f Dockerfile .
#

FROM alpine:3.5

RUN cd ~ && \
    apk add --no-cache python && \
    apk add --no-cache --virtual .builddep curl  gcc python-dev&& \
    curl -OL https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-137.0.1-linux-x86_64.tar.gz && \
    tar xf google-cloud-sdk-137.0.1-linux-x86_64.tar.gz && \
    ./google-cloud-sdk/install.sh \
        -q --usage-reporting=false && \
    ./google-cloud-sdk/bin/gcloud components update && \
    apk del --purge .builddep && \
    rm -fr /var/cache/apk/* \
           /root/google-cloud-sdk-137.0.1-linux-x86_64.tar.gz
