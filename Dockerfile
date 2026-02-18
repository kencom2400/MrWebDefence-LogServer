# Fluentd LogServer Dockerfile
# Base: Fluentd official image
FROM fluent/fluentd:v1.16-debian-1

# Switch to root for plugin installation
USER root

# Install required plugins
RUN gem install \
    fluent-plugin-rewrite-tag-filter \
    fluent-plugin-prometheus \
    && gem sources --clear-all

# Create necessary directories
RUN mkdir -p /var/log/mrwebdefence \
    && mkdir -p /var/log/fluentd/buffer \
    && mkdir -p /var/log/fluentd/invalid \
    && mkdir -p /var/log/fluentd/unmatched \
    && mkdir -p /etc/fluentd/certs \
    && chown -R fluent:fluent /var/log/mrwebdefence \
    && chown -R fluent:fluent /var/log/fluentd \
    && chown -R fluent:fluent /etc/fluentd/certs

# Switch back to fluent user
USER fluent

# Expose ports
# 8888: Log receiver (HTTPS)
# 8889: Health check
# 24220: Monitor agent
# 24231: Prometheus metrics
EXPOSE 8888 8889 24220 24231

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8889/health || exit 1

# Start Fluentd
CMD ["fluentd", "-c", "/fluentd/etc/fluent.conf"]
