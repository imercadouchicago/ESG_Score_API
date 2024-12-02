FROM python:3.13.0-alpine AS base

WORKDIR /app/src

#  Add Selenium dependencies
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

# Prevents creation of .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Enable more consistent printing
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

# Install packages in requirements.txt
COPY requirements.txt /app/src
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Run Flask app on Gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]