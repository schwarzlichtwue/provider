FROM alpine
ENV SOURCE_REPO=/source_repo
ENV TARGET_REPO=/target_repo
ENV ROOT=/app
ENV GIT_MAIL=schwarzlicht.wuerzburg@gmail.com
ENV GIT_NAME=schwarzlichtwue
ENV GIT_REPO=git@github.com:schwarzlichtwue/schwarzlichtwue.github.io.git
ENV GIT_SOURCE_BRANCH=dev
ENV GIT_TARGET_BRANCH=master
RUN mkdir $ROOT && mkdir $ROOT/db/ && mkdir $SOURCE_REPO && mkdir $TARGET_REPO

RUN apk update && apk upgrade && apk add --no-cache python3 openssh git ruby-dev ruby build-base sshpass lftp tor
RUN gem install --no-document jekyll bundler bigdecimal jekyll-paginate-v2
RUN if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi
RUN if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi

RUN pip3 install --upgrade pip


WORKDIR $ROOT

COPY ./id_rsa $ROOT/id_rsa
RUN mkdir ~/.ssh && echo -e "Host github.com\n\tStrictHostKeyChecking=no\n\tUser git\n\tIdentityFile $ROOT/id_rsa\n\nHost www3.systemli.org\n\tUser schwarzlicht\n\tStrictHostKeyChecking=no\n\tDynamicForward 127.0.0.1:9050" >> ~/.ssh/config
RUN git config --global user.email $GIT_MAIL && git config --global user.name $GIT_NAME
RUN eval `/usr/bin/ssh-agent` && ssh-add $ROOT/id_rsa && git clone $GIT_REPO $SOURCE_REPO
RUN cp -r $SOURCE_REPO/. $TARGET_REPO/

RUN cd $SOURCE_REPO && git checkout $GIT_SOURCE_BRANCH && bundle install
RUN cd $TARGET_REPO && git checkout $GIT_TARGET_BRANCH && cd $ROOT

COPY . $ROOT/

RUN python3 setup.py install

ENTRYPOINT ["./entrypoint.sh"]
