all:
	nbdev_export
	#nbdev_export --path  nbs/__init__.ipynb
	nbdev_docs
export:
	nbdev_export
	#nbdev_export --path  nbs/__init__.ipynb

# Install libs that are not present by default
libs:
	mamba install -y pyproj
	mamba install -y geographiclib

navconstants_export:
	nbdev_export --path nbs/NavConstants.ipynb

navdatainstall:
	cp -v 2023*csv.gz /opt/nav

install:
	pip install ../NavLib

dev_install:
	pip install -e .
    
uninstall:
	pip uninstall  NavLib
    
preview:
	nbdev_preview

docs:
	nbdev_docs
    
deploy:
	nbdev_deploy
    
bump:
	nbdev_bump_version

clean:
	nbdev_clean
	echo "clean Not setup yet.  All done" 
