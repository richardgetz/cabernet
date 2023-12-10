FROM python:3.8-alpine
RUN apk add --no-cache --update bash tzdata ffmpeg curl && \
    apk add --no-cache --virtual builddeps gcc musl-dev python3-dev libffi-dev openssl-dev cargo && \
    pip3 install requests && \
    pip3 install cryptography && \
    apk del builddeps
COPY *.py /app/
COPY lib/ /app/lib/
COPY plugins /app/plugins
COPY plugins_ext /app/plugins_ext
RUN touch /app/is_container
ENTRYPOINT ["python3", "/app/tvh_main.py"]