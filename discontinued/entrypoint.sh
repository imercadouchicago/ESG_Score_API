#!/bin/bash

# Start Xvfb on display :1 (or another display if needed)
echo "Starting Xvfb..."
Xvfb :1 -screen 0 1024x768x16 &

# Wait a moment for Xvfb to initialize
sleep 2

# Now we can change the ownership of /tmp/.X11-unix
echo "Changing ownership of /tmp/.X11-unix..."
chown root:root /tmp/.X11-unix

# Now execute the parallel scraping script
echo "Running parallel scraping..."
python /app/src/parallel_scraper.py
