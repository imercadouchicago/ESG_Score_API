FROM python:3.13.0-alpine AS base
WORKDIR /app/src

RUN apk update && apk add --no-cache \
    chromium \
    chromium-chromedriver \
    harfbuzz \
    ttf-freefont \
    fontconfig \
    libx11 \
    libxcomposite \
    libxrandr \
    libxi \
    libxtst \
    libxdamage \
    libxfixes \
    mesa-dri-gallium \
    mesa-egl \
    udev \
    cups-libs \
    nss
RUN pip install --upgrade pip

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user that the app will run under.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/bin/sh" \
    --uid "${UID}" \
    appuser

# Use BuildKit cache mounts for pip and requirements.txt file
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]
