# appgateway

Appgateway is a tool for fetching Android apps from various sources, verifying their integrity and publishing them over a F-Droid repository.
At the moment their are two input sources available: https and PlayStore Packages
All activities will be logged to `/var/log/appgateway.log'

## Requirements
The tool relies on `gplacli` (https://github.com/matlink/gplaycli) for the PlayStore interface and `fdroidserver` (https://gitlab.com/fdroid/fdroidserver) for providing the repo.

## Configuration
The configuration file must be placed at /etc/appgateway/appgateway.conf
A example configuration (with placeholders) is given in appgateway_example.conf

### Syntax

Every app is a section in the INI-like conf file, with one exception,  the META section. 

	[META]
	repo = /var/www/repo # fdroid repository
	apk_store = /var/apkstore # where the downloaded apps are stored
	archive = /var/apkstore_archive # future use backup store
	credentials = /etc/gplay/credentials.conf # appstore credentials (see gplacli documentation)
	
	[<APP ID>]
	source = <playstore or https >
	url = <url> # only necessary for https sources
	cert_sha256 = <hash> # SHA256 of the developers certificate
	

## App verification
Every downloaded App will be verified. This means that first the sha256sum of the developer certificate in `META-INF/CERT.RSA` will be compared with the value from the configuration file and after that `jarsigner` will be called to check the APK's integrity. I really don't know if this is the correct or the best way to do it, but it's the best I could come up with. If you know it better, please let me know.


## Easy deployment
I'm currently working on a docker container with a full functional setup for easy deployment
