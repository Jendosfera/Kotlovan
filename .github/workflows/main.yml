name: Build Android APK

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            build-essential \
            python3-pip \
            git \
            autoconf \
            automake \
            libtool \
            pkg-config \
            zlib1g-dev \
            libncurses5-dev \
            libreadline-dev \
            libsqlite3-dev \
            libssl-dev \
            libbz2-dev \
            liblzma-dev \
            tk-dev \
            libffi-dev \
            curl \
            wget \
            unzip \
            openjdk-17-jdk \
            ant \
            cmake

      - name: Install Buildozer and Cython
        run: |
          pip install buildozer "cython<3"

      - name: Pre-accept Android SDK licenses
        run: |
          mkdir -p /home/runner/.buildozer/android/platform/android-sdk/cmdline-tools/latest
          wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdline-tools.zip
          unzip -q /tmp/cmdline-tools.zip -d /tmp/cmdline-tools
          mv /tmp/cmdline-tools/cmdline-tools/* /home/runner/.buildozer/android/platform/android-sdk/cmdline-tools/latest/
          yes | /home/runner/.buildozer/android/platform/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=/home/runner/.buildozer/android/platform/android-sdk --licenses

      - name: Build APK
        run: |
          buildozer -v android debug

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: kotlovan-apk
          path: bin/*.apk
          retention-days: 7
