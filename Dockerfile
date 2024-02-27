FROM python:3-slim
RUN apt-get update && apt-get install vim -y
RUN pip install --upgrade pip && pip install requests pyyaml pandas
RUN pip install google-auth google-cloud-core google-cloud-vision 
RUN pip install openai scikit-image tenacity
CMD ["tail", "-f", "/dev/null"]