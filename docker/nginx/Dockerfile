FROM nginx:stable-alpine
COPY curl2share/static /etc/nginx/html/static
COPY docker/nginx/conf/file_system.conf /etc/nginx/conf.d/default.conf
CMD ["nginx", "-g", "daemon off;"]
EXPOSE 8888 80 
