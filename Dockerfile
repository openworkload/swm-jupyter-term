FROM jupyterhub/jupyterhub:5.2.1

RUN pip install --no-cache-dir swmjupyter
RUN mkdir /root/.swm
