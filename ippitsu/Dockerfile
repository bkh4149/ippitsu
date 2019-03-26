FROM tiangolo/uwsgi-nginx-flask:python3.6

RUN apt update && apt -y install gcc libsasl2-dev && apt -y install net-tools

# ソースを置くディレクトリを変数として設定
ARG project_dir=/var/www
ARG web_app_dir=$project_dir/trend

# 必要なファイルをローカルからコンテナ内にコピー
ADD . $project_dir/

# 環境変数設定
ENV UWSGI_INI $web_app_dir/uwsgi.ini
ENV PYTHONPATH=$web_app_dir
#ENV STATIC_INDEX 1

# pipパッケージをインストール
RUN cd $project_dir && pip install -r requirements.txt
WORKDIR $web_app_dir

# Expose ports.
EXPOSE 5000