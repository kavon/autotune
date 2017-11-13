#!/bin/bash

# inputs: MK, PASSES

make -f ${MK} bitcode
make -f ${MK} optimize
make -f ${MK} link
time make -f ${MK} run
time make -f ${MK} run
time make -f ${MK} run
