FROM python:3.10



# install FreeTDS and dependencies
# RUN apt-get update \
#  && apt-get install unixodbc -y \
#  && apt-get install unixodbc-dev -y \
#  && apt-get install freetds-dev -y \
#  && apt-get install freetds-bin -y \
#  && apt-get install tdsodbc -y \
#  && apt-get install --reinstall build-essential -y
# # populate "ocbcinst.ini" as this is where ODBC driver config sits
# RUN echo "[FreeTDS]\n\
# Description = FreeTDS Driver\n\
# Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
# Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini




RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#Download appropriate package for the OS version
#Choose only ONE of the following, corresponding to your OS version
#Debian 11
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN exit
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18


WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN mkdir logs

RUN touch ./logs/logfile.log

COPY main.py AzSql.py PSql.py log.ini ./

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--log-config", "./log.ini"] 