FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Potential Problem Line (Startup Script)
RUN /bin/sh -c "cat /mount/admin/install_path && python A2.py"

CMD ["streamlit", "run", "A2.py"]
