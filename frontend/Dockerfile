FROM nginx:alpine

# Copy static frontend assets to Nginx default html directory
COPY frontend/ /usr/share/nginx/html/

# Copy custom Nginx server configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
