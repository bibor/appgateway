#! /usr/bin/python2
# -*- coding: utf-8 -*-
"""
appgateway by bibor

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
details.
You should have received a copy of the GNU Affero General Public License along with this program.  If not,
see <http://www.gnu.org/licenses/>.
"""


import sys
import os
import argparse
import ConfigParser
import logging
import shutil
import requests
import subprocess
from gplaycli.gplaycli import GPlaycli


class AppGateway:
    def __init__(self, confFile="/etc/appgateway/appgateway.conf", logfile="/var/log/appgateway.log"):
        logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        self.logfile=logfile
        logging.info("started appgateway")
        if not os.path.isfile(confFile):
            logging.critical("Config File not found in %s", confFile)
            sys.exit(-1)
        self.confFile = confFile
        self.configparser = ConfigParser.SafeConfigParser()
        self.configparser.read(self.confFile)

        if self.configparser.has_option("META", "repo"):
            self.repodir = self.configparser.get("META", "repo")
        else:
            errormsg = "Repo directory was not found in configfile"
            logging.critical(errormsg)
            print(errormsg)
            sys.exit(-1)

        if self.configparser.has_option("META", "apk_store"):
            self.apk_store = self.configparser.get("META", "apk_store")
        else:
            errormsg = "apk store directory was not found in configfile"
            logging.critical(errormsg)
            print(errormsg)
            sys.exit(-1)

        if self.configparser.has_option("META", "fdroid_dir"):
            self.fdroid_dir = self.configparser.get("META", "fdroid_dir")
        else:
            errormsg = "fdroid directory was not found in configfile"
            logging.critical(errormsg)
            print(errormsg)
            sys.exit(-1)

        self.tempdir = "/tmp/appgateway/"
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        else:
            shutil.rmtree(self.tempdir)
            os.mkdir(self.tempdir)

    def fullRun(self):
        logging.info("started a full run")
        self.loadallApps()
        self.updateFdroid()
        logging.info("completed full run")
        sys.exit(0)

    def loadallApps(self):
        logging.debug("loadallapps")
        playstoreapps =[]
        httpsapps = []
        for app in self.configparser.sections():
            if app != "META":
                if self.configparser.get(app, "source") == "playstore":
                    playstoreapps.append(app)
                elif self.configparser.get(app, "source") == "https":
                    httpsapps.append(app)
                else:
                    print("skipping " + app + ", unrecognised source")
                    logging.warning("skipping %s, unrecognised source", app)
        self.loadPlayStoreApps(playstoreapps)
        self.loadHttpsApps(httpsapps)


    def verifyandmove(self, apps):
        print("verifiying apps...")
        for app in apps:
            appfile = os.path.join(self.tempdir, app + ".apk")
            if AppGateway.verifyApk(app, appfile, self.configparser.get(app, "cert_sha256")):
                logging.info("verified %s", app)
                if os.path.isfile(os.path.join(self.apk_store, app +".apk")):
                    os.remove(os.path.join(self.apk_store, app +".apk"))
                shutil.move(appfile, self.apk_store)
            else:
                print("VERIFICATION ERROR: " + appfile + "could not be verified")
                logging.error("%s could not be verfied. apk will be removed", appflile)
                os.remove(appfile)

    @staticmethod
    def verifyApk(app, appfile, sha256_wanted):
        getRawCert = subprocess.Popen(["unzip", "-p", appfile, "META-INF/CERT.RSA"], stdout=subprocess.PIPE)
        cert_is = subprocess.check_output(["keytool", "-printcert"], stdin=getRawCert.stdout)
        getRawCert.wait()
        lines = cert_is.split("\n")
        for line in lines:
            if "SHA256" in line:
                sha256_is = line.split(": ")[1]
        if sha256_wanted != sha256_is:
            return False
        else:
            jarsign_out = subprocess.check_output(["jarsigner", "-verify", appfile])
            if ("jar verified." in jarsign_out) and not ("This jar contains unsigned entries which have not been integrity-checked." in jarsign_out):
                return True
            else:
                return False


    def loadPlayStoreApps(self, apps):
        cli = GPlaycli()
        cli.yes = True
        cli.verbose = False
        cli.progress_bar = True
        success, error = cli.connect_to_googleplay_api()
        if not success:
            logging.critical("Cannot  login to GooglePlay (%s)", error)
            print("Cannot login to GooglePlay (", error, ")")
            sys.exit(1)
        cli.set_download_folder(self.tempdir)
        logging.info("Bulk download playstore packages..")
        print("bulk load playstore packages: \n" + str(apps))
        for app in apps:
            logging.info("Bulk playstore download: %s", app)
        # maybe patch to get not loaded packages, maybe use rather cli.download_selection
        cli.download_packages(apps)
        self.verifyandmove(apps)


    def downloadHttpsApp(self, app):
        url = self.configparser.get(app, "url")
        if "https://" in url:
            logging.info("https download: %s", app)
            print("http download: " + app)
            filename = os.path.join(self.tempdir, app + ".apk")
            r = requests.get(url, stream=True)
            with open(filename, 'wb') as fil:
                shutil.copyfileobj(r.raw, fil)
            return True
        elif "http://" in url:
            errormsg = "does not provide a https link and will be skipped"
            print (apk + " " + errormsg)
            logging.warning("%s %s", app, errormsg)
            return False
        else:
            errormsg = "shit got wrong, yo with"
            print(errormsg + " " + app)
            logging.warning("%s %s", errormsg, app)
            return False


    def loadHttpsApps(self, apps):
        for app in apps:
           self.downloadHttpsApp(app)
        self.verifyandmove(apps)

    def updateFdroid(self):
        logging.info("updating Fdroid")

        fdroid = subprocess.Popen(["fdroid","update", "-c"], cwd=self.fdroid_dir)
        fdroid.wait()
        #clean up repo
        if os.path.exists(os.path.join(self.repodir, "repo")):
            shutil.rmtree(os.path.join(self.repodir, "repo"))
        #cp apk_store to repo
        shutil.copytree(self.apk_store, os.path.join(self.repodir, "repo"))



def main():
    cliparser = argparse.ArgumentParser()
    cliparser.add_argument("-a", "--all", action="store_true", dest="full_run", help="perform complete run")
    if len(sys.argv) < 2:
        sys.argv.append("-h")
    args = cliparser.parse_args()
    appgw = AppGateway()
    if args.full_run:
        appgw.fullRun()
    else:
        logging.info("exited with nothing to do")
        sys.exit(0)



if __name__ == '__main__':
    main()
