FROM python:3.14-bookworm

ARG _USER="pygitops"
ARG _UID="1000"
ARG _GID="100"
ARG _SHELL="/bin/bash"

# Install uv as root before creating the user
ENV UV_NO_CACHE="true"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    cp /root/.local/bin/uvx /usr/local/bin/uvx

RUN useradd -m -s "${_SHELL}" -N -u "${_UID}" "${_USER}"

ENV USER=${_USER}
ENV UID=${_UID}
ENV GID=${_GID}
ENV HOME=/home/${_USER}
ENV PATH="${HOME}/.local/bin/:${PATH}"

RUN mkdir /app && chown ${UID}:${GID} /app

# Copy requirements files as root since we'll install as root
COPY ./requirements* /app/
WORKDIR /app

# Install from lock file (contains all deps: main, test, docs)
RUN uv pip install --system -r requirements.lock

# Change ownership of app directory to user
RUN chown -R ${UID}:${GID} /app

USER ${_USER}

CMD bash
