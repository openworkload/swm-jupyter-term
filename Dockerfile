FROM jupyterhub/jupyterhub:6.0.1

WORKDIR /srv/jupyterhub

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY swmjupyter /srv/jupyterhub/swmjupyter

RUN pip install --no-cache-dir \
        "jinja2" \
        "jupyterhub-nativeauthenticator" \
        "oauthenticator" \
        "swmclient>=0.1.7" \
    && useradd --create-home --uid 1000 --shell /bin/bash jupyterhub \
    && mkdir -p /home/jupyterhub/.swm/spool/secure/cluster \
                /var/lib/swmjupyter/uploads \
    && chown -R jupyterhub:jupyterhub \
        /srv/jupyterhub \
        /home/jupyterhub \
        /var/lib/swmjupyter

ENV PYTHONPATH=/srv/jupyterhub \
    HOME=/home/jupyterhub \
    SWM_JUPYTER_AUTH=native \
    SWM_JUPYTER_BIND_IP=127.0.0.1 \
    SWM_JUPYTER_BIND_PORT=8000 \
    SWM_JUPYTER_UPLOAD_ROOT=/var/lib/swmjupyter/uploads

USER jupyterhub

CMD ["/usr/local/bin/jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
