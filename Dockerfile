FROM mxmp/python-netsnmp:python3

WORKDIR /
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt
RUN rm requirements.txt

COPY . /app
WORKDIR /app