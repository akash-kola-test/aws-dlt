FROM blazemeter/taurus:1.16.34

RUN /usr/bin/python3 -m pip install --upgrade pip \
    && pip install --no-cache-dir awscli

RUN rm -rf /root/.bzt/selenium-taurus \
    rm -rf /root/.bzt/gatling-taurus \
    rm -rf /usr/share/dotnet \
    && apt remove -y k6

COPY ./load-test.sh /bzt-configs/
RUN chmod 755 /bzt-configs/load-test.sh

WORKDIR /bzt-configs/

ENTRYPOINT [ "./load-test.sh" ]
