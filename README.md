# appgateway

Appgateway is a tool for fetching Android apps from various sources, verifying their integrity and publishing them over a F-Droid repository.
At the moment their are two input sources available: https and PlayStore Packages
All activities will be logged to `/var/log/appgateway.log'

## Requirements
The tool relies on `gplacli` (https://github.com/matlink/gplaycli) for the PlayStore interface and `fdroidserver` (https://gitlab.com/fdroid/fdroidserver) for providing the repo.

### Issues
Commit `61ed5aa6f1e3cae7beecc7f1375ae86b0b70cba5` of `gplaycli` breakes `appgateway`. I've forked a working version (https://github.com/bibor/gplaycli).

## Configuration
The configuration file must be placed at /etc/appgateway/appgateway.conf
A example configuration (with placeholders) is given in appgateway_example.conf

### Syntax
Every app is a section in the INI-like conf file, with one exception,  the META section. 

    [META]
    repo = /var/www/html/
    apk_store = /var/fdroid/repo
    fdroid_dir = /var/fdroid
    archive = /var/apkstore_archive
    credentials = /etc/gplay/credentials.conf
	
	[<APP ID>]
	source = <playstore or https >
	url = <url> # only necessary for https sources
	cert_sha256 = <hash> # SHA256 of the developers certificate
	

## App verification
The integrity of all downloaded apps will be verified through `apksigner`. The SHA256 sum of the signer's cert will be compared to the one, given in the config file.

## Easy deployment
I'm currently working on a docker container with a full functional setup for easy deployment
