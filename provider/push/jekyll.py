import os
import subprocess
import logging

class Jekyll(object):
    def __init__(self, source_folder: str, target_folder: str):
        self.source_folder = source_folder
        self.target_folder = target_folder

    def build(self):
        logging.info(
            "Performing jekyll build of {}. Writing to {}".format(
            self.source_folder, self.target_folder)
            )
        cmd = ['cd {} && JEKYLL_ENV="production" jekyll build -d {}'.format(self.source_folder,
            self.target_folder)]
        subprocess.run(cmd, shell=True)
        logging.info("Jekyll build finished")
