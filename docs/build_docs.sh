# Custom bash script to generate the ampycloud docs
# Created for dvas in June 2020; F.P.A. Vogt; frederic.vogt@meteoswiss.ch
# Adapted to ampycloud in December 2021; F.P.A. Vogt; frederic.vogt@meteoswiss.ch
#

# Step 0: clean the existing Sphinx apidoc rst files and any previous build folder.
# Make sure to not delete any important .git info for the CI auto_publish action !
# Note: "find" crashes if the directory does not exist ... which is the case for some of the
# Github Actions, hence the if ...  then ... else below. fpavogt, 2020-12-14.
rm -rf ./source/modules
if [ -d "./build" ]
then
    echo "Smart cleaning of the ./build directory."
    find ./build -not \( -path '*.git*' -o -name '.nojekyll' -o -name '.-gitignore' \) -delete
else
    echo "FYI: directory ./build does not exists yet and is therefore not cleaned."
fi

# Step 1: run autodoc to generate all the docstring rst files.
# Force the rewrite of all of them to capture *all* the recent changes.
sphinx-apidoc -f -M -o ./source/modules/ ../src/

# Delete the superfluous module.rst file that the previous command creates.
rm -f ./source/modules/modules.rst

# Save the ampycloud_speed_test help and actual performance,
# to automate the display of this information in the docs.
ampycloud_speed_test -h > source/ampycloud_speed_test_help_msg.txt
ampycloud_speed_test > source/ampycloud_speed_test_msg.txt

# Generate the documentation, storing it in the build directory
sphinx-build -a -b html ./source ./build

# Clean-up
rm source/ampycloud_speed_test_help_msg.txt
rm source/ampycloud_speed_test_msg.txt
