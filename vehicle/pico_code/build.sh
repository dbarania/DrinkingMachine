
export PICO_SDK_PATH=../pico-sdk

if [[ $1 == "--reset" ]]; then
    rm -rf build
    mkdir build
fi

if [[ ! -d build ]]; then
    mkdir build
fi
cd build || exit

cmake ..
make
