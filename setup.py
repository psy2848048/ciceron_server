from setuptools import setup, find_packages
import subprocess


print ("This setup script runs with 'root' user on Ubuntu linux only!")

linux_dependencies = [
        "python-virtualenv"
      , "libssl-dev"
      , "libffi-dev"
      , "redis-server"
      , "libxml2-dev"
      , "libxslt1-dev"
      , "python-dev"
      , "nodejs"
      , "nodejs-dev"
      # , "postgresql"
      , "postgresql-contrib"
      , "libpq-dev"
        ]

subprocess.call("apt-get --yes install %s" % " ".join(linux_dependencies))

setup(
        name='ciceron_server'
      , version='0.9.1'
      , auther='Bryan RHEE'
      , author_email='junhang.lee@ciceeron.me'
      , packages=find_packages()
      , install_requires=[
                      , "Flask"
                      , "requests"
                      , "paypalrestsdk"
                      , "flask-cors"
                      , "flask-redis"
                      , "flask-session"
                      , "Flask-Pushjack"
                      , "Flask-Cache"
                      , "Flask-OAuth"
                      , "python-docx"
                      , "lxml"
                      , "alipay"
                      , "psycopg2"
                      , "iamport-rest-client"
                      , "nltk"
                      , "google-api-python-client"
                      , "microsofttranslator"
                      , "yandex.translate"
                      , "python-i18n"
                      , "nslocalized"
                      , "xmltodict"
                    ]
        )

import nltk
print ("Setup NLTK into the server. Please install all pickles, and wait for a few minute.")
print ("If the script freezes, you may press CTRL+C to break!")
nltk.download()
