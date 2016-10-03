#!/bin/bash
set -e

install_ice() {
  git clone https://github.com/ice-stuff/ice
  pushd ice
    # build a wheel release
    pip install wheel
    ./hack/build

    # install iCE
    pip install dist/*.whl
  popd
}

install_dev_deps() {
  pip install -r dev-requirements.txt
}

install_ice
install_dev_deps
