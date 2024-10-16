# Cry Baby Hadi

Cry Baby is a small piece of software which provides a probability that your baby is crying by continuously recording audio, chunking it into 4-second clips, and feeding them into a Convolutional Neural Network (CNN).
It is made to run on macOS or linux, with a few added dependencies to install for Raspberry pi (Bookworm 64-bit).

It is configured to send a message to a MQTT cluster on threshold detection.

## Acknowledgments
Based on Cry Baby : [BaronBonnet's Cry baby](https://github.com/BaronBonet/cry-baby). This project has been largely based on cry baby with a few tweaks for my needs. All credit goes to them for making this awesome project.

## Installation

1. Prepare your hardware if needed
  - flash the microSD card with Bookworm 64-bit
  - setup wi-fi and ssh
  - Update locale

``` bash
locale
sudo update-locale LC_ALL="en_GB.UTF-8"
sudo update-locale LANGUAGE="en_GB:en"
```

2. [OPTIONAL] Install the dependencies for Raspberry pi
``` bash
sudo apt install git python3-pip
sudo apt install portaudio19-dev
sudo apt install libsndfile1
```

3. Clone the repository
``` bash
git clone https://github.com/obenchekroun/cry-baby-hadi
cd cry-baby-hadi
```

4. Create a virtual environnement and activate it
``` bash
python3 -m venv .venv # to create
source .venv/bin/activate
```

in order to deactivate the virtual environnement, you can use `deactivate`, `exit` or *ctrl-D*

5. Install the dependencies with Poetry using the command :
``` bash
pip3 install poetry
poetry install
```

Depending on your hardware architecture, Poetry should automatically install the correct version of TensorFlow or TensorFlow Lite. Tested on Mabook Pro M2 Max (2023) and Rpi 4 (bookworm 64-bit)..

6. setup your huggingface token : 
You will need a [hugging face account](https://huggingface.co/welcome) and an API token. Once you have the token, copy `example.env` to `.env` and add your token there. If you want to use MQTT posting and notification, you need to also put your MQTT credentials and websocket address in this file. Otherwise, remove all the MQTT lines.

``` bash
cp .example.env .env
nano .env
```

``` bash
HUGGING_FACE_TOKEN="<your-token>"
MQTT_SERVER="<your-server>"
MQTT_USER="<your-username>"
MQTT_PASSWORD="<your-password>"
```

7. *[OPTIONAL]* Setup MQTT Push client on your phone to receive notifications

## Usage
A Makefile is provided for running Cry Baby.

```bash
make run
```

Every 4 seconds, Cry Baby will print the probability of a baby crying in each audio clip it records. And saves the timestamp, a pointer to the audio file, and the probability to a CSV file.


### Setting up a `systemd` service on startup

- Configure and start a `systemd` service to launch on startup :
```bash
sudo chmod +x run.sh # make the run script executable
cp cry-baby-hadi.service.template cry-baby-hadi.service
nano cry-baby-hadi.service
```
Edit the file with the correct paths to the scripts and the project.

- Then to enable the service
``` bash
sudo mv cry-baby-hadi.service /etc/systemd/system
sudo systemctl enable cry-baby-hadi.service #to launch service on startup
sudo systemctl daemon-reload
sudo journalctl -u cry-baby-hadi.service #to get journal
```

- The service can be started, stopped, restarted and checked :
``` bash
$ sudo systemctl start cry-baby-hadi.service
$ sudo systemctl stop cry-baby-hadi.service
$ sudo systemctl restart cry-baby-hadi.service
$ systemctl status cry-baby-hadi.service
```


## About the model

The codebase for training the model is currently not included in this repository due to its preliminary state. See original repository for updates.

### Training data

The model was trained on 1.2 GB of evenly distributed labeled audio files, consisting of both crying and non-crying samples.

Data sources include:

- [Ubenwa CryCeleb2023](https://huggingface.co/datasets/Ubenwa/CryCeleb2023)
- [ESC-50 Dataset for environmental sound classification](https://dagshub.com/kinkusuma/esc50-dataset), also featuring non-crying samples
- Audio clips downloaded from YouTube, such as [this one](https://www.youtube.com/watch?v=lmbJP1yObZc)
- Friends who were willing to record there babies crying

### Preprocessing

The raw audio files were processed into 4-second Mel Spectrogram clips using [Librosa](https://librosa.org/doc/0.10.1/generated/librosa.feature.melspectrogram.html#librosa.feature.melspectrogram), which provides a two-dimensional representation of the sound based on the [mel-scale frequencies](https://en.wikipedia.org/wiki/Mel_scale).

The preprocessing routine is integral to Cry Baby's runtime operations and is available [here](./cry_baby/pkg/audio_file_client/adapters/librosa_client.py).

### Dataset partitioning

The dataset underwent an initial split: 80% for training and the remaining 20% for validation and testing. The latter was further divided equally between validation and testing.

### Model architecture

The model's architecture is inspired by the design presented in [this research paper](https://www.pacet-conf.gr/Files/PACET2022paper194.pdf). Below is a visualization of the model structure:

![CNN Model visualized](https://cdn.ericcbonet.com/baby-cry-cnn-model-visualization.png?)

### Training and evaluation

Training was conducted over 10 epochs with a batch size of 32. The corresponding training and validation loss and accuracy metrics are illustrated below.

![loss and accuracy metrics](https://cdn.ericcbonet.com/cry-baby-accuracy-loss-metrics.png?)
