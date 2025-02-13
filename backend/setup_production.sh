#!/bin/bash

# Create necessary directories
mkdir -p /home/app/fiat/backend/uploads
mkdir -p /home/app/fiat/backend/static

# Create default images directory
mkdir -p /home/app/fiat/backend/static/images

# Set proper permissions
chown -R www-data:www-data /home/app/fiat/backend/uploads
chown -R www-data:www-data /home/app/fiat/backend/static
chmod 755 /home/app/fiat/backend/uploads
chmod 755 /home/app/fiat/backend/static

# Set environment variables
echo "FLASK_ENV=production" >> /etc/environment
echo "BASE_URL=http://167.99.157.245" >> /etc/environment

# Restart nginx and your Flask application
systemctl restart nginx
# Replace 'your-flask-service' with your actual service name
# systemctl restart your-flask-service
