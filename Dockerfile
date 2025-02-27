FROM python:3.9-slim-buster

WORKDIR /Steam

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Potential Problem Line (Startup Script)
RUN /bin/sh -c "cat /mount/admin/install_path && python A1.py"

CMD ["streamlit", "run", "A1.py"]
