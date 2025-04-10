FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]