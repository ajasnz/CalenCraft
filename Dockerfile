FROM python:3.12-alpine3.17
WORKDIR /usr/src/cc


COPY . ./
RUN pip3 install -r requirements.txt


RUN mkdir /usr/src/cc/app/config
VOLUME [ "/usr/src/cc/app/config" ]

EXPOSE 8088

CMD ["python3", "./app/server.py"]
