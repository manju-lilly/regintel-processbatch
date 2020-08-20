#!/bin/sh

# This runs the install phase of the build.
#
# To run outside CodeBuild, set the following variables before running:
# CODEBUILD_SRC_DIR
#   Set this to your project's root directory.

install_tools() {
  echo "Installing AWS SAM CLI"
  pip install aws-sam-cli

  echo "Installing CloudFormation template linting tool cfn-lint"
  pip install cfn-lint

  echo "Installing Python code linting tool pylint"
  pip install pylint

  echo "Installing Python testing tool pytest"
  pip install pytest
}

install_dependencies() {
  echo "Installing Node.js code dependencies"
  for function_directory in ${CODEBUILD_SRC_DIR}/functions/* ; do
    cd ${function_directory}
    if [ -f "package.json" ]; then
      echo "  Installing dependencies for ${function_directory}"
      npm install
    fi
  done

  echo "Installing Python code dependencies"
  for function_directory in ${CODEBUILD_SRC_DIR}/functions/* ; do
    cd ${function_directory}
    if [ -f "requirements.txt" ]; then
      echo "  Installing dependencies for ${function_directory}"
      pip install -r requirements.txt
    fi
  done
}

install_python_layer() {
  LAYER_PATH=${PWD}/python
  echo "  Installing Python layer in ${LAYER_PATH}"

  cd ${LAYER_PATH}
  if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -t . --upgrade
  fi

  if [ "${PYTHONPATH#*LAYER_PATH}" = "${PYTHONPATH}" ]; then
    if [ "${PYTHONPATH}" = "" ]; then
      export PYTHONPATH=${LAYER_PATH}
    else
      export PYTHONPATH=${LAYER_PATH}:${PYTHONPATH}
    fi
  fi
}

install_nodejs_layer() {
  LAYER_PATH=${PWD}/nodejs
  NODE_MODULES_DIR=${LAYER_PATH}/node_modules
  echo "  Installing NodeJS layer in ${LAYER_PATH}"

  cd ${LAYER_PATH}
  if [ -f "package.json" ]; then
    npm install
  fi

  if [ "${NODE_PATH#*$LAYER_PATH}" = "${NODE_PATH}" ]; then
   if [ "$NODE_PATH" = "" ]; then
     export NODE_PATH=${NODE_MODULES_DIR}
   else
     export NODE_PATH=${NODE_MODULES_DIR}:${NODE_PATH}
   fi
  fi
}

install_layers() {
  echo "Installing Lambda layers"
  for layer_directory in ${CODEBUILD_SRC_DIR}/layers/*; do
    cd ${layer_directory}
    if [ -d "python" ]; then
      install_python_layer
    elif [ -d "nodejs" ]; then
      install_nodejs_layer
    fi
  done
  echo "NODE_PATH=${NODE_PATH}"
  echo "PYTHONPATH=${PYTHONPATH}"
}

echo "Starting install - $(date)"
STARTING_DIR=$PWD

install_tools
install_dependencies
install_layers

cd $STARTING_DIR
unset STARTING_DIR
echo "Completed install - $(date)"