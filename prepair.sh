#!/bin/bash
set -e

cd gnuboxmaker/kernel_build
../../syslbuild.py --arch ALL kernel_build.json
cd ../..

rm -rf gnuboxmaker/kernel_image
mkdir -p gnuboxmaker/kernel_image
cp -r gnuboxmaker/kernel_build/output/* gnuboxmaker/kernel_image/.
