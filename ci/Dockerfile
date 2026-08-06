# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CI_ARTIFACTS=/artifacts

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates git nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app/package.json app/package-lock.json /workspace/app/
RUN npm --prefix app ci --no-audit --no-fund

COPY . /workspace

# Dependencies are already inside the image. The launcher runs this image with
# --network none so the tests themselves cannot depend on external services.
ENTRYPOINT ["python", "ci/run_ci.py"]
CMD ["autopilot"]
