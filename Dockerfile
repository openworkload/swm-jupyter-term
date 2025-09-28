FROM jupyterhub/jupyterhub:5.2.1

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

RUN pip install --no-cache-dir swmjupyter
RUN mkdir /root/.swm

CMD ["/usr/local/bin/jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
