FROM jupyterhub/jupyterhub:6.0.1

WORKDIR /srv/jupyterhub

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY swmjupyter /srv/jupyterhub/swmjupyter

RUN pip install --no-cache-dir \
        "jinja2" \
        "jupyterhub-nativeauthenticator" \
        "oauthenticator" \
        "swmclient>=0.1.7" \
    && mkdir -p /root/.swm

ENV PYTHONPATH=/srv/jupyterhub \
    SWM_JUPYTER_AUTH=native \
    SWM_JUPYTER_BIND_IP=127.0.0.1 \
    SWM_JUPYTER_BIND_PORT=8000

CMD ["/usr/local/bin/jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
