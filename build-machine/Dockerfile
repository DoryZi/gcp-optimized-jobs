from docker:latest

RUN apk add --no-cache python py2-pip curl bash
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:~/google-cloud-sdk/bin

RUN pip install docker-compose



