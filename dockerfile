FROM python:3

ADD __mysql.py /
ADD btc.py /

RUN pip install sqlalchemy

RUN pip install pandas

RUN pip install cbpro

RUN pip install pymysql

RUN pip install urllib3

ENV TZ=America/Chicago

EXPOSE 3306

ENTRYPOINT ["python", "./btc.py"]