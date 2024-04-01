FROM texlive/texlive:TL2023-historic

RUN set -xe \
    && apt-get update \
    && apt-get install -y vim \
    && apt-get install -y python3.12 python3-pip python3-venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip

WORKDIR /diff_test_tex_engines
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the tex sources over to be safe
# docker_bin is provided as a volume
COPY bin/arxiv_tars_extracted /diff_test_tex_engines/bin/tex_sources

# files needed to run compile_only.py
COPY compile_only.py .
COPY compile_only_2.py .
COPY pipeline/compile_tex_files.py pipeline/compile_tex_files.py
COPY utils utils
COPY constants constants

