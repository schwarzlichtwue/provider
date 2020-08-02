# Twitter Content Provider

## Shortest possible summary

Listens for tweets of a defined twitter account, transforms the tweet into a
__jekyll__ post and pushes the changes to a __github-pages__ repository.

## A more detailed description

This is a python application that archives tweets of a defined twitter account.
The application is deployed via docker. All tweets are added to an __sqlite__
database and, in regular intervals, transformed to jekyll posts. New posts are
pushed to a git repository hosted by github.com and to another hoster via sftp.
All syncing/pushing is done via __TOR__.
