all:
	nbdev_export
	nbdev_docs
export:
	nbdev_export

dev_install:
	pip install -e .
    
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
