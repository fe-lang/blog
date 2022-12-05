.PHONY: build
build:
	zola build
.PHONY: serve
serve:
	zola serve
.PHONY: deploy
deploy: build
		echo -e "\033[0;32mDeploying blog...\033[0m"
		# delete old gh-pages-tmp + gh-pages-dist branch if they exists
		-git branch -D gh-pages-tmp gh-pages-dist

		# Recreate it
		git checkout -b gh-pages-tmp

		# Add changes to git.
		git add -f target

		# Commit changes.
		git commit -m "Generated blog"

		# Only preserve target as the root of contents for this branch
		git subtree split -P target -b gh-pages-dist

		# Push to Github Pages
		git push -f upstream gh-pages-dist:gh-pages

		# Go where we came from
		git checkout -

		# Delete temporary branches
		git branch -D gh-pages-tmp
		git branch -D gh-pages-dist
