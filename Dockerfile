FROM python:3.13-slim

RUN useradd -m appuser
USER appuser

WORKDIR /home/appuser/src

ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONPATH=/home/appuser/src

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=appuser:appuser src/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
