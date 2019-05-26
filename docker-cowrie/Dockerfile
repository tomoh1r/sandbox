#
# Build Cowrie on Alpine Linux.
#
# Usage:
#   $ docker build -t local/cowrie -f Dockerfile .
#

FROM alpine:3.5

# master revision
ENV MY_REV=dcabed5

RUN apk add --no-cache python ca-certificates bash python-dev libcrypto1.0 libssl1.0 gmp mpfr3 mpc1 &&\
    apk add --no-cache --virtual .builddep curl su-exec gcc python-dev musl-dev libffi-dev openssl-dev gmp-dev mpfr-dev mpc1-dev unzip && \
    curl -L https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    python /tmp/get-pip.py &&\
    python -m pip install virtualenv &&\

    adduser -D -h /cowrie cowrie &&\
    cd /cowrie &&\
        su-exec cowrie curl -L https://codeload.github.com/micheloosterhof/cowrie/zip/${MY_REV} -o cowrie.zip &&\
        su-exec cowrie unzip cowrie.zip &&\
        su-exec cowrie mv cowrie-${MY_REV} cowrie-master &&\
        cd cowrie-master &&\
            su-exec cowrie virtualenv --clear cowrie-env &&\
            su-exec cowrie cowrie-env/bin/python /tmp/get-pip.py &&\
            su-exec cowrie cowrie-env/bin/python -m pip install -r requirements.txt &&\
            su-exec cowrie sed -i -E 's/DAEMONIZE=""/DAEMONIZE="-n"/g' bin/cowrie &&\
            su-exec cowrie ln -sfn etc/cowrie.cfg cowrie.cfg &&\
    cd ~ &&\

    apk del --purge .builddep && \
    rm /tmp/get-pip.py &&\
    rm /cowrie/cowrie.zip &&\
    rm -fr /var/cache/apk/*

USER cowrie
WORKDIR /cowrie

EXPOSE 2222 2223
VOLUME ["/cowrie/cowrie-master/etc", "/cowrie/cowrie-master/var"]

CMD ./cowrie-master/bin/cowrie start
