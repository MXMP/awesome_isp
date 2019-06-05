FROM mxmp/python-netsnmp:python3

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requdirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run core.py when the container launches
CMD ["python3", "core.py"]