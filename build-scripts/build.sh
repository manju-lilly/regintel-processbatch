#!/bin/sh

# This runs the build phase of the build.
#
# To run outside CodeBuild, set the following variables before running:
# TEMPLATE_PATH
#   Set this to the path to the template.yml file at the root of your project.
# S3_DEPLOY_BUCKET
#   Set this to the name of an S3 bucket you control.
#
# Be sure you are logged in to AWS, as this script uploads to S3.

build_application() {
  sam build --template-file ${TEMPLATE_PATH}
}

package_application() {
  ### YOU MUST SPECIFY A KMS KEY TO USE WHEN PACKAGING YOUR TEMPLATE ###
  sam package --template-file .aws-sam/build/template.yaml --kms-key-id alias/aws/s3 --s3-bucket ${S3_DEPLOY_BUCKET} --output-template-file ${TEMPLATE_PATH}
}

echo "Starting build - $(date)"
build_application
package_application
echo "Completed build - $(date)"
