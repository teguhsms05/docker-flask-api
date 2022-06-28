#Create a ubuntu base image with python 3 installed.
FROM python:3.9.7

#Set the working directory
WORKDIR /app

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

#Expose the required port
EXPOSE 5005

#Run the command
CMD gunicorn main:app

#Expose the required port
#EXPOSE 5000

#Run the command
#CMD gunicorn --bind 0.0.0.0:5000 main:app