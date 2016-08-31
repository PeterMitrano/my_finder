# My Finder [![Build Status](https://travis-ci.org/PeterMitrano/my_finder.svg?branch=master)](https://travis-ci.org/PeterMitrano/my_finder)

An alexa skill for remembering where you put stuff!

"Alexa, tell My Finder I put my keys in my tableside drawer"
"Alexa, tell My Finder I left my wallet in the blue bin
"Alexa, tell My Finder I put my shoes in the bottom of the closet

.. eons later ...

"Alexa, ask My Finder where I put my wallet"

_Your wallet is in the blue bin_

"Alexa, ask My Finder where I left the keys"

_Your keys are in my tableside drawer bin_


"Alexa, ask My Finder where my shoes are"

_Your shoes are in the bottom of the cloest

_Your keys are in my tableside drawer bin_

## NLTK

nltk is a dependency of this project. Make sure you run the following:

    mkdir nltk_data
    export NLTK_DATA ./nltk_data
    python -m nltk.downloader wordnet

Because of wordnet, make sure to use as much RAM as possible on lambda.
