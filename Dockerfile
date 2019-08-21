FROM alpine
ENV REPO=/repo
ENV ROOT=/app
ENV GIT_MAIL=schwarzlicht.wuerzburg@gmail.com
ENV GIT_NAME=schwarzlichtwue
ENV GIT_REPO=git@github.com:schwarzlichtwue/schwarzlichtwue.github.io.git
ENV GIT_BRANCH=dev
RUN mkdir $ROOT && mkdir $ROOT/db/ && mkdir $REPO

RUN apk update && apk upgrade && apk add --no-cache python3 openssh git ruby-dev ruby build-base
RUN gem install --no-document jekyll bundler bigdecimal
RUN if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi
RUN if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi

RUN pip3 install --upgrade pip


WORKDIR $ROOT

COPY ./id_rsa $ROOT/id_rsa
RUN mkdir ~/.ssh && echo -e "Host github.com\n\tStrictHostKeyChecking no\n\tUser git\n\tIdentityFile $ROOT/id_rsa\n" >> ~/.ssh/config
RUN git config --global user.email $GIT_MAIL && git config --global user.name $GIT_NAME
RUN eval `/usr/bin/ssh-agent` && ssh-add $ROOT/id_rsa && git clone $GIT_REPO $REPO

RUN cd $REPO && git checkout $GIT_BRANCH && bundle install && cd $ROOT

COPY ./ $ROOT/

RUN python3 setup.py install

ENTRYPOINT ["content-provider", "-e", "/app/.env", "-s", "/app/id_rsa", "-d", "/app/db/db.sqlite3", "-u", "4", "-g", "/repo"]
