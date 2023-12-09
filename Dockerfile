#may work with earlier versions of python tho
FROM python:3.11.6
ADD bot.py .
ADD CONFIG.py .
ADD NAMES.py .
ADD sailordb.py .
COPY requirements.txt ./
RUN pip install -r requirements.txt
CMD ["python3", "./bot.py"]
